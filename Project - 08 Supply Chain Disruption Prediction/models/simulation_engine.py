"""
Toyota Motor Corporation - Counterfactual What-If Scenario Simulation Engine
Project - 08: Supply Chain Disruption Prediction

Enables interactive testing of global operational stress scenarios:
- Maritime port dwell surges (e.g. Long Beach / Southampton strikes)
- Critical supplier capacity shocks (e.g. Semiconductor or EV Battery shortages)
- Severe weather & canal chokepoint transit delays
- Buffer inventory policies (Rigid JIT vs. AI-Dynamic Resilient Buffer)
- Automated mitigation execution (Real-time prevention of assembly stoppages)
"""

import numpy as np
import pandas as pd

class SimulationEngine:
    def __init__(self, df, reg_model=None, feature_names=None):
        self.df = df.copy()
        self.reg_model = reg_model
        self.feature_names = feature_names

    def simulate_scenario(self, 
                          port_dwell_additional_days=0.0,
                          supplier_capacity_drop_pct=0.0,
                          weather_severity_multiplier=1.0,
                          buffer_strategy="dynamic_ai",
                          mitigation_active=True):
        """
        Runs a counterfactual simulation on a sample cohort of 1,000 active shipments
        to calculate real-time operational risk, downtime hours, and financial exposure.
        """
        # Sample 1,000 realistic active shipments
        sample_df = self.df.sample(n=min(1200, len(self.df)), random_state=42).copy()
        
        # Apply Port Dwell Shock
        sample_df['sim_port_dwell'] = sample_df['port_dwell_time_days'] + port_dwell_additional_days
        
        # Apply Supplier Capacity Shock
        sample_df['sim_capacity_util'] = np.clip(
            sample_df['supplier_capacity_util_pct'] * (1.0 + (supplier_capacity_drop_pct / 100.0)),
            50.0, 125.0
        )
        
        # Apply Weather Shock
        sample_df['sim_weather'] = np.clip(
            sample_df['weather_risk_index'] * weather_severity_multiplier,
            1.0, 10.0
        )
        
        # Buffer Strategy
        if buffer_strategy == "rigid_jit":
            # Traditional lean JIT: minimal safety stock, no dynamic buffer
            sample_df['sim_dos'] = sample_df['days_of_supply'] * 0.8
        elif buffer_strategy == "dynamic_ai":
            # AI Adaptive Buffer: elevated safety stock on high-volatility corridors
            sample_df['sim_dos'] = sample_df['days_of_supply'] * 1.35
        else:
            sample_df['sim_dos'] = sample_df['days_of_supply']
            
        sample_df['sim_safety_ratio'] = sample_df['sim_dos'] / sample_df['safety_stock_threshold_days']
        
        # Transit Delay propagation
        sample_df['sim_delay_days'] = np.clip(
            sample_df['actual_delay_days'] + (port_dwell_additional_days * 0.7) + 
            ((sample_df['sim_weather'] - 3.0) * 0.5 if weather_severity_multiplier > 1.0 else 0),
            0.0, 30.0
        )
        
        # Calculate simulated disruption probability
        sim_vuln = (
            (1.0 - sample_df['supplier_otd_rate']) * 35.0 +
            np.maximum(0, 1.2 - sample_df['sim_safety_ratio']) * 45.0 +
            (sample_df['sim_delay_days'] / np.maximum(1.0, sample_df['sim_dos'] * 2.0)) * 25.0 +
            (sample_df['single_source_flag'] * 18.0) +
            (sample_df['sim_port_dwell'] > 5.0) * 15.0 +
            (sample_df['sim_weather'] > 6.0) * 12.0 +
            (sample_df['sim_capacity_util'] > 95.0) * 15.0
        )
        
        sim_prob = 1.0 / (1.0 + np.exp(-(sim_vuln - 48.0) / 10.0))
        sample_df['sim_disrupted'] = (sim_prob > 0.48).astype(int)
        
        # Downtime calculation
        base_downtime = np.where(
            sample_df['sim_disrupted'] == 1,
            np.clip(
                (sample_df['sim_delay_days'] * 1.8) + 
                (sample_df['sim_port_dwell'] * 0.6) + 
                (sample_df['single_source_flag'] * 6.0) - 
                (sample_df['sim_dos'] * 1.5),
                2.0, 48.0
            ),
            0.0
        )
        
        if mitigation_active:
            # AI Prescriptive Interventions (Air-Bridge, Heijunka Resequence, Buffer Pull)
            # Eliminate 88% of downtime
            mitigated_downtime = base_downtime * 0.12
            mitigation_cost = np.where(sample_df['sim_disrupted'] == 1, 45000.0, 0.0)
        else:
            mitigated_downtime = base_downtime
            mitigation_cost = 0.0
            
        unmitigated_loss = base_downtime * sample_df['hourly_downtime_cost_usd']
        mitigated_loss = (mitigated_downtime * sample_df['hourly_downtime_cost_usd']) + mitigation_cost
        
        # Summary metrics
        total_shipments_simulated = len(sample_df)
        disrupted_shipments = int(sample_df['sim_disrupted'].sum())
        disruption_rate_pct = round((disrupted_shipments / total_shipments_simulated) * 100, 1)
        
        unmitigated_hours_total = round(float(np.sum(base_downtime)), 1)
        mitigated_hours_total = round(float(np.sum(mitigated_downtime)), 1)
        hours_saved = round(unmitigated_hours_total - mitigated_hours_total, 1)
        
        unmitigated_loss_millions = round(float(np.sum(unmitigated_loss)) / 1e6, 2)
        mitigated_loss_millions = round(float(np.sum(mitigated_loss)) / 1e6, 2)
        net_savings_millions = round(unmitigated_loss_millions - mitigated_loss_millions, 2)
        
        # Resilience index (0-100 score)
        resilience_index = round(float(np.clip(
            100.0 - (disruption_rate_pct * 0.8) - (mitigated_hours_total / 20.0),
            15.0, 98.0
        )), 1)
        
        # Plant impact count
        impacted_plants = sample_df[sample_df['sim_disrupted'] == 1]['plant_name'].nunique()

        return {
            "total_shipments_simulated": total_shipments_simulated,
            "disrupted_shipments": disrupted_shipments,
            "disruption_rate_pct": disruption_rate_pct,
            "impacted_plants_count": impacted_plants,
            "unmitigated_downtime_hours": unmitigated_hours_total,
            "mitigated_downtime_hours": mitigated_hours_total,
            "downtime_hours_saved": hours_saved,
            "unmitigated_financial_loss_millions": unmitigated_loss_millions,
            "mitigated_financial_loss_millions": mitigated_loss_millions,
            "net_financial_savings_millions": net_savings_millions,
            "resilience_index": resilience_index,
            "mitigation_active": mitigation_active,
            "parameters": {
                "port_dwell_additional_days": port_dwell_additional_days,
                "supplier_capacity_drop_pct": supplier_capacity_drop_pct,
                "weather_severity_multiplier": weather_severity_multiplier,
                "buffer_strategy": buffer_strategy
            }
        }

if __name__ == "__main__":
    df = pd.read_csv("data/toyota_supply_chain_telemetry.csv")
    sim = SimulationEngine(df)
    res = sim.simulate_scenario(port_dwell_additional_days=5.0, supplier_capacity_drop_pct=25.0, buffer_strategy="rigid_jit", mitigation_active=False)
    print("Baseline Stress (No Mitigation):", res)
    res2 = sim.simulate_scenario(port_dwell_additional_days=5.0, supplier_capacity_drop_pct=25.0, buffer_strategy="dynamic_ai", mitigation_active=True)
    print("AI Mitigated Stress:", res2)

