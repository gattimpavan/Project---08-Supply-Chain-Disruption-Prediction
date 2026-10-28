"""
Toyota Motor Corporation - Supply Chain Disruption & Telemetry Data Generator
Project - 08: Supply Chain Disruption Prediction

Synthesizes high-fidelity, realistic enterprise telemetry for Toyota's global manufacturing ecosystem:
- 6 Global Assembly Plants (Tsutsumi, Tahara, Motomachi, Kentucky TMMK, Indiana TMMI, UK TMUK)
- 7 Critical Part Categories (Semiconductor ECUs, Li-Ion Batteries, Wire Harnesses, Transmissions, Stamped Steel, Steering/Suspension, ADAS Sensors)
- 18 Tier-1 & Tier-2 Key Suppliers (Denso, Renesas, Bosch, Primearth EV, Yazaki, Sumitomo, Aisin, etc.)
- Multi-modal Freight & Global Logistics Corridors (Maritime, Intermodal Rail, Air Freight, Cross-Border Trucking)
- Dynamic Inventory Buffer, Kanban Depletion Velocity, and Assembly Line Stoppage Telemetry
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Seed for reproducibility
np.random.seed(42)

PLANTS = [
    {
        "plant_id": "PLANT-JPN-01",
        "plant_name": "Tsutsumi Assembly Plant",
        "location": "Toyota City, Japan",
        "region": "Japan/APAC",
        "models": "Prius, RAV4, Camry",
        "daily_target_units": 1500,
        "hourly_downtime_cost_usd": 1850000,  # $1.85M/hr
        "takt_time_sec": 58
    },
    {
        "plant_id": "PLANT-JPN-02",
        "plant_name": "Tahara Assembly Plant",
        "location": "Aichi, Japan",
        "region": "Japan/APAC",
        "models": "Land Cruiser, Lexus LS, Lexus NX",
        "daily_target_units": 1100,
        "hourly_downtime_cost_usd": 2400000,  # $2.4M/hr (High-margin luxury)
        "takt_time_sec": 65
    },
    {
        "plant_id": "PLANT-JPN-03",
        "plant_name": "Motomachi Assembly Plant",
        "location": "Toyota City, Japan",
        "region": "Japan/APAC",
        "models": "Crown, bZ4X EV, Mirai, GR Yaris",
        "daily_target_units": 850,
        "hourly_downtime_cost_usd": 2100000,  # $2.1M/hr (Flagship/EV)
        "takt_time_sec": 72
    },
    {
        "plant_id": "PLANT-USA-01",
        "plant_name": "Toyota Motor Mfg Kentucky (TMMK)",
        "location": "Georgetown, Kentucky, USA",
        "region": "North America",
        "models": "Camry, RAV4 Hybrid, Grand Highlander",
        "daily_target_units": 1800,
        "hourly_downtime_cost_usd": 2250000,  # $2.25M/hr
        "takt_time_sec": 54
    },
    {
        "plant_id": "PLANT-USA-02",
        "plant_name": "Toyota Motor Mfg Indiana (TMMI)",
        "location": "Princeton, Indiana, USA",
        "region": "North America",
        "models": "Highlander, Sienna Minivan, Lexus TX",
        "daily_target_units": 1350,
        "hourly_downtime_cost_usd": 1950000,  # $1.95M/hr
        "takt_time_sec": 60
    },
    {
        "plant_id": "PLANT-EUR-01",
        "plant_name": "Toyota Motor Mfg UK (TMUK)",
        "location": "Burnaston, Derbyshire, UK",
        "region": "Europe",
        "models": "Corolla Hatchback, Corolla Touring Sports",
        "daily_target_units": 950,
        "hourly_downtime_cost_usd": 1650000,  # $1.65M/hr
        "takt_time_sec": 62
    }
]

SUPPLIERS = [
    {"supplier_id": "SUP-101", "name": "Denso Corporation", "country": "Japan", "tier": "Tier-1", "primary_category": "Semiconductor ECUs", "single_source": 0, "base_otd": 0.96, "base_defect_ppm": 12},
    {"supplier_id": "SUP-102", "name": "Renesas Electronics", "country": "Japan", "tier": "Tier-1", "primary_category": "Semiconductor ECUs", "single_source": 1, "base_otd": 0.88, "base_defect_ppm": 35},
    {"supplier_id": "SUP-103", "name": "Bosch Automotive", "country": "Germany", "tier": "Tier-1", "primary_category": "ADAS & LiDAR Sensors", "single_source": 0, "base_otd": 0.94, "base_defect_ppm": 18},
    {"supplier_id": "SUP-104", "name": "Primearth EV Energy (PEVE)", "country": "Japan", "tier": "Tier-1", "primary_category": "Lithium-Ion Battery Modules", "single_source": 1, "base_otd": 0.91, "base_defect_ppm": 24},
    {"supplier_id": "SUP-105", "name": "Panasonic Energy", "country": "Japan", "tier": "Tier-1", "primary_category": "Lithium-Ion Battery Modules", "single_source": 0, "base_otd": 0.95, "base_defect_ppm": 15},
    {"supplier_id": "SUP-106", "name": "Yazaki Corporation", "country": "Japan", "tier": "Tier-1", "primary_category": "Wire Harnesses & Connectors", "single_source": 0, "base_otd": 0.87, "base_defect_ppm": 48},
    {"supplier_id": "SUP-107", "name": "Sumitomo Electric Wiring", "country": "Japan", "tier": "Tier-1", "primary_category": "Wire Harnesses & Connectors", "single_source": 0, "base_otd": 0.89, "base_defect_ppm": 42},
    {"supplier_id": "SUP-108", "name": "Aisin Corporation", "country": "Japan", "tier": "Tier-1", "primary_category": "Transmission & Differential", "single_source": 0, "base_otd": 0.97, "base_defect_ppm": 10},
    {"supplier_id": "SUP-109", "name": "Toyota Boshoku", "country": "Japan", "tier": "Tier-1", "primary_category": "Interior Systems & Stamped Steel", "single_source": 0, "base_otd": 0.96, "base_defect_ppm": 14},
    {"supplier_id": "SUP-110", "name": "JTEKT Corporation", "country": "Japan", "tier": "Tier-1", "primary_category": "Steering & Suspension", "single_source": 0, "base_otd": 0.95, "base_defect_ppm": 16},
    {"supplier_id": "SUP-111", "name": "Nippon Steel Corp", "country": "Japan", "tier": "Tier-2", "primary_category": "Interior Systems & Stamped Steel", "single_source": 1, "base_otd": 0.90, "base_defect_ppm": 28},
    {"supplier_id": "SUP-112", "name": "Continental AG", "country": "Germany", "tier": "Tier-1", "primary_category": "ADAS & LiDAR Sensors", "single_source": 0, "base_otd": 0.92, "base_defect_ppm": 22},
    {"supplier_id": "SUP-113", "name": "TSMC (Silicon Foundry)", "country": "Taiwan", "tier": "Tier-2", "primary_category": "Semiconductor ECUs", "single_source": 1, "base_otd": 0.85, "base_defect_ppm": 38},
    {"supplier_id": "SUP-114", "name": "CATL Battery Technology", "country": "China", "tier": "Tier-1", "primary_category": "Lithium-Ion Battery Modules", "single_source": 0, "base_otd": 0.90, "base_defect_ppm": 32},
    {"supplier_id": "SUP-115", "name": "Lear Corporation", "country": "USA", "tier": "Tier-1", "primary_category": "Wire Harnesses & Connectors", "single_source": 0, "base_otd": 0.91, "base_defect_ppm": 29},
    {"supplier_id": "SUP-116", "name": "ZF Friedrichshafen", "country": "Germany", "tier": "Tier-1", "primary_category": "Transmission & Differential", "single_source": 0, "base_otd": 0.93, "base_defect_ppm": 20},
    {"supplier_id": "SUP-117", "name": "Magna International", "country": "Canada", "tier": "Tier-1", "primary_category": "Interior Systems & Stamped Steel", "single_source": 0, "base_otd": 0.93, "base_defect_ppm": 21},
    {"supplier_id": "SUP-118", "name": "Mobis Parts", "country": "South Korea", "tier": "Tier-2", "primary_category": "Steering & Suspension", "single_source": 0, "base_otd": 0.89, "base_defect_ppm": 34}
]

PARTS_CATALOG = [
    {"part_id": "PART-ECU-01", "name": "Hybrid Engine Management ECU", "category": "Semiconductor ECUs", "lead_time_days": 45, "unit_cost_usd": 680, "criticality": "Critical"},
    {"part_id": "PART-ECU-02", "name": "TSS 3.0 Autonomous Driving ECU", "category": "Semiconductor ECUs", "lead_time_days": 55, "unit_cost_usd": 1150, "criticality": "Critical"},
    {"part_id": "PART-BAT-01", "name": "71.4 kWh Li-Ion Traction Battery Pack", "category": "Lithium-Ion Battery Modules", "lead_time_days": 35, "unit_cost_usd": 4800, "criticality": "Critical"},
    {"part_id": "PART-BAT-02", "name": "Bipolar NiMH Hybrid Battery Module", "category": "Lithium-Ion Battery Modules", "lead_time_days": 28, "unit_cost_usd": 1450, "criticality": "High"},
    {"part_id": "PART-HAR-01", "name": "Main Cockpit Wire Harness (High-Voltage)", "category": "Wire Harnesses & Connectors", "lead_time_days": 21, "unit_cost_usd": 520, "criticality": "Critical"},
    {"part_id": "PART-HAR-02", "name": "Chassis Low-Voltage Harness Assembly", "category": "Wire Harnesses & Connectors", "lead_time_days": 18, "unit_cost_usd": 280, "criticality": "Medium"},
    {"part_id": "PART-TRN-01", "name": "Direct Shift e-CVT Transaxle", "category": "Transmission & Differential", "lead_time_days": 25, "unit_cost_usd": 2400, "criticality": "Critical"},
    {"part_id": "PART-TRN-02", "name": "Dynamic Torque Vectoring Rear Differential", "category": "Transmission & Differential", "lead_time_days": 20, "unit_cost_usd": 1200, "criticality": "High"},
    {"part_id": "PART-STL-01", "name": "Ultra-High Tensile Stamped Roof Rail Steel", "category": "Interior Systems & Stamped Steel", "lead_time_days": 14, "unit_cost_usd": 380, "criticality": "High"},
    {"part_id": "PART-STL-02", "name": "Front Sub-Frame Structural Cast Member", "category": "Interior Systems & Stamped Steel", "lead_time_days": 12, "unit_cost_usd": 450, "criticality": "Medium"},
    {"part_id": "PART-STR-01", "name": "Electric Power Steering (EPS) Actuator", "category": "Steering & Suspension", "lead_time_days": 16, "unit_cost_usd": 620, "criticality": "High"},
    {"part_id": "PART-STR-02", "name": "Adaptive Variable Suspension Shock Absorber", "category": "Steering & Suspension", "lead_time_days": 18, "unit_cost_usd": 310, "criticality": "Medium"},
    {"part_id": "PART-SNS-01", "name": "Millimeter-Wave Radar Radar Unit", "category": "ADAS & LiDAR Sensors", "lead_time_days": 30, "unit_cost_usd": 490, "criticality": "Critical"},
    {"part_id": "PART-SNS-02", "name": "High-Definition Monocular Forward Camera Sensor", "category": "ADAS & LiDAR Sensors", "lead_time_days": 32, "unit_cost_usd": 540, "criticality": "Critical"}
]

LOGISTICS_CORRIDORS = [
    {"corridor_id": "CORR-01", "mode": "Maritime_Container", "origin": "Nagoya Port (Japan)", "dest": "Long Beach Port (USA)", "base_days": 18, "weather_risk_mean": 3.2, "port_dwell_mean": 3.5},
    {"corridor_id": "CORR-02", "mode": "Maritime_Container", "origin": "Yokohama (Japan)", "dest": "Port of Southampton (UK)", "base_days": 26, "weather_risk_mean": 4.1, "port_dwell_mean": 4.2},
    {"corridor_id": "CORR-03", "mode": "Intermodal_Rail", "origin": "Long Beach Port (USA)", "dest": "Georgetown Yard (Kentucky)", "base_days": 5, "weather_risk_mean": 2.1, "port_dwell_mean": 1.2},
    {"corridor_id": "CORR-04", "mode": "Cross_Border_Trucking", "origin": "Monterrey (Mexico)", "dest": "Princeton Plant (Indiana)", "base_days": 3, "weather_risk_mean": 2.4, "port_dwell_mean": 1.8},
    {"corridor_id": "CORR-05", "mode": "Domestic_Trucking_JIT", "origin": "Aichi Supplier Hub (Japan)", "dest": "Tsutsumi Plant (Japan)", "base_days": 1, "weather_risk_mean": 1.5, "port_dwell_mean": 0.4},
    {"corridor_id": "CORR-06", "mode": "Domestic_Trucking_JIT", "origin": "Aichi Supplier Hub (Japan)", "dest": "Tahara Plant (Japan)", "base_days": 1, "weather_risk_mean": 1.6, "port_dwell_mean": 0.4},
    {"corridor_id": "CORR-07", "mode": "Air_Freight_Charter", "origin": "Tokyo Haneda (Japan)", "dest": "Cincinnati CVG Hub (USA)", "base_days": 2, "weather_risk_mean": 2.0, "port_dwell_mean": 0.8},
    {"corridor_id": "CORR-08", "mode": "Maritime_Container", "origin": "Kaohsiung (Taiwan)", "dest": "Nagoya Port (Japan)", "base_days": 6, "weather_risk_mean": 4.8, "port_dwell_mean": 2.8},
    {"corridor_id": "CORR-09", "mode": "Intermodal_Rail", "origin": "Hamburg Port (Germany)", "dest": "Midlands Freight Terminal (UK)", "base_days": 4, "weather_risk_mean": 3.0, "port_dwell_mean": 2.1}
]

def generate_supply_chain_dataset(num_records=15000, output_dir="data"):
    """
    Generates synthetic but operationally rigorous Toyota supply chain dataset.
    Simulates real-world manufacturing telemetry across 4 interconnected tiers:
    1. Supplier health and reliability
    2. Inventory buffer and Kanban velocity
    3. Multimodal transit and corridor bottlenecks
    4. Assembly plant production scheduling and line stoppage risk
    """
    os.makedirs(output_dir, exist_ok=True)
    
    records = []
    start_date = datetime(2026, 1, 1)
    
    for i in range(num_records):
        # Sample Plant
        plant = PLANTS[np.random.choice(len(PLANTS))]
        
        # Sample Part
        part = PARTS_CATALOG[np.random.choice(len(PARTS_CATALOG))]
        
        # Match supplier capable of supplying this part category
        matching_suppliers = [s for s in SUPPLIERS if s["primary_category"] == part["category"]]
        if not matching_suppliers:
            supplier = SUPPLIERS[np.random.choice(len(SUPPLIERS))]
        else:
            supplier = matching_suppliers[np.random.choice(len(matching_suppliers))]
            
        # Select appropriate corridor based on geography
        if "Japan" in plant["location"] and supplier["country"] == "Japan":
            corridor = [c for c in LOGISTICS_CORRIDORS if c["corridor_id"] in ["CORR-05", "CORR-06"]][0]
        elif "USA" in plant["location"] and supplier["country"] == "Japan":
            corridor = [c for c in LOGISTICS_CORRIDORS if c["corridor_id"] in ["CORR-01", "CORR-03", "CORR-07"]][np.random.choice([0, 1, 2], p=[0.75, 0.20, 0.05])]
        elif "UK" in plant["location"] and supplier["country"] in ["Germany", "UK"]:
            corridor = [c for c in LOGISTICS_CORRIDORS if c["corridor_id"] == "CORR-09"][0]
        elif "USA" in plant["location"] and supplier["country"] == "USA":
            corridor = [c for c in LOGISTICS_CORRIDORS if c["corridor_id"] == "CORR-04"][0]
        elif supplier["country"] == "Taiwan":
            corridor = [c for c in LOGISTICS_CORRIDORS if c["corridor_id"] == "CORR-08"][0]
        else:
            corridor = LOGISTICS_CORRIDORS[np.random.choice(len(LOGISTICS_CORRIDORS))]
            
        # Timestamp
        date_offset = np.random.randint(0, 300)
        timestamp = start_date + timedelta(days=date_offset, hours=np.random.randint(0, 24))
        
        # --- 1. Supplier Telemetry ---
        # Base supplier performance with random variance and stress spikes
        stress_event = np.random.binomial(1, 0.12)  # 12% probability of supplier stress event
        
        supplier_otd = np.clip(supplier["base_otd"] - (0.25 * stress_event) + np.random.normal(0, 0.03), 0.50, 0.99)
        defect_ppm = int(np.clip(supplier["base_defect_ppm"] * (1.0 + 3.0 * stress_event) + np.random.normal(0, 5), 5, 450))
        supplier_capacity_util = np.clip(np.random.normal(82, 10) + (15 * stress_event), 55.0, 108.0)
        supplier_fin_risk = int(np.clip(np.random.normal(25, 12) + (35 * stress_event) + (10 if supplier["single_source"] else 0), 5, 95))
        lead_time_variance_days = np.clip(np.random.normal(0.5, 1.2) + (6.0 * stress_event), -2.0, 28.0)
        
        # --- 2. Inventory & Buffer Telemetry ---
        # Toyota lean JIT target is usually 2.0 to 3.5 days of safety stock
        # In a disruption, days of supply crashes below 1.5 days
        base_safety_threshold = np.round(np.random.uniform(1.8, 3.2), 1)
        
        # Inventory depletion factors
        inventory_shock = np.random.binomial(1, 0.14)
        if inventory_shock:
            days_of_supply = np.round(np.clip(np.random.uniform(0.3, 1.6), 0.2, 8.0), 2)
        else:
            days_of_supply = np.round(np.clip(np.random.normal(base_safety_threshold + 0.8, 0.7), 1.2, 9.0), 2)
            
        safety_stock_ratio = np.round(days_of_supply / base_safety_threshold, 2)
        daily_consumption = int(plant["daily_target_units"] * np.random.uniform(0.9, 1.1))
        current_stock_units = int(days_of_supply * daily_consumption)
        
        if safety_stock_ratio < 0.6:
            kanban_status = "Critical_Buffer_Breach"
        elif safety_stock_ratio < 1.0:
            kanban_status = "Reorder_Triggered"
        else:
            kanban_status = "Adequate"
            
        # --- 3. Transportation & Corridor Telemetry ---
        weather_shock = np.random.binomial(1, 0.10)
        weather_risk_index = np.round(np.clip(corridor["weather_risk_mean"] + (4.5 * weather_shock) + np.random.normal(0, 0.8), 1.0, 10.0), 1)
        
        port_congestion_shock = np.random.binomial(1, 0.15)
        port_dwell_days = np.round(np.clip(corridor["port_dwell_mean"] + (6.0 * port_congestion_shock) + np.random.normal(0, 1.0), 0.2, 18.0), 1)
        
        carrier_reliability = np.round(np.clip(np.random.normal(0.92, 0.05) - (0.20 * port_congestion_shock), 0.50, 0.99), 2)
        
        scheduled_transit_days = corridor["base_days"]
        actual_delay_days = np.round(np.clip(
            (0.5 * port_dwell_days) + 
            (0.8 * (weather_risk_index - 3.0) if weather_risk_index > 3.0 else 0) + 
            lead_time_variance_days * 0.4 + 
            np.random.normal(0, 1.0), 
            0.0, 24.0
        ), 1)
        total_projected_transit_days = scheduled_transit_days + actual_delay_days
        
        # --- 4. Disruption Ground Truth & Operational Impact ---
        # Disruption occurs when inventory buffer runs out before replenishment arrives
        # Early warning signal calculation
        vulnerability_score = (
            (1.0 - supplier_otd) * 35.0 +
            (max(0, 1.2 - safety_stock_ratio) * 45.0) +
            (actual_delay_days / max(1.0, days_of_supply * 2.0)) * 25.0 +
            (supplier["single_source"] * 18.0) +
            (1.0 if part["criticality"] == "Critical" else 0.5) * 12.0 +
            (port_dwell_days > 5.0) * 15.0 +
            (weather_risk_index > 6.0) * 12.0
        )
        
        disruption_prob = 1.0 / (1.0 + np.exp(-(vulnerability_score - 48.0) / 10.0))
        disruption_occurred = 1 if np.random.uniform(0, 1) < disruption_prob else 0
        
        # Severity categorization
        if disruption_occurred:
            if vulnerability_score > 78 or (safety_stock_ratio < 0.4 and actual_delay_days > 4):
                disruption_severity = "Critical"
                projected_downtime_hours = np.round(np.random.uniform(14.0, 36.0), 1)
                days_to_line_stoppage = np.round(np.clip(days_of_supply * 0.8, 0.2, 3.5), 1)
            elif vulnerability_score > 62:
                disruption_severity = "High"
                projected_downtime_hours = np.round(np.random.uniform(6.0, 14.0), 1)
                days_to_line_stoppage = np.round(np.clip(days_of_supply * 1.2, 1.0, 5.0), 1)
            else:
                disruption_severity = "Moderate"
                projected_downtime_hours = np.round(np.random.uniform(1.5, 6.0), 1)
                days_to_line_stoppage = np.round(np.clip(days_of_supply * 1.8, 2.5, 9.0), 1)
        else:
            if vulnerability_score > 42:
                disruption_severity = "Low"
                projected_downtime_hours = 0.0
                days_to_line_stoppage = np.round(np.random.uniform(10.0, 25.0), 1)
            else:
                disruption_severity = "Nominal"
                projected_downtime_hours = 0.0
                days_to_line_stoppage = np.round(np.random.uniform(20.0, 45.0), 1)
                
        # Financial loss calculation (hourly downtime cost * hours)
        financial_loss_usd = np.round(projected_downtime_hours * plant["hourly_downtime_cost_usd"], 2)
        
        # Recommended AI Autonomous Action
        if disruption_severity == "Critical":
            if supplier["single_source"]:
                recommended_action = "Emergency Air-Bridge Charter & Dynamic Heijunka Resequence"
            else:
                recommended_action = "Dual-Source PO Ramp-up (80/20 Shift) & Cross-Plant Kanban Pull"
        elif disruption_severity == "High":
            if corridor["mode"] == "Maritime_Container":
                recommended_action = "Expedite Intermodal Rail & Dynamic Regional Safety Buffer Reallocation"
            else:
                recommended_action = "Safety Stock Kanban Buffer Elevation & Shift Re-scheduling"
        elif disruption_severity == "Moderate":
            recommended_action = "Proactive Supplier Expedite Notice & In-transit Prioritization"
        elif disruption_severity == "Low":
            recommended_action = "Routine Telemetry Monitoring & Standard Kanban Replenishment"
        else:
            recommended_action = "Nominal Lean JIT Operations Maintained"
            
        record = {
            "record_id": f"TYT-SC-{100000 + i}",
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "plant_id": plant["plant_id"],
            "plant_name": plant["plant_name"],
            "plant_location": plant["location"],
            "plant_region": plant["region"],
            "affected_models": plant["models"],
            "plant_daily_target_units": plant["daily_target_units"],
            "hourly_downtime_cost_usd": plant["hourly_downtime_cost_usd"],
            "part_id": part["part_id"],
            "part_name": part["name"],
            "part_category": part["category"],
            "part_criticality": part["criticality"],
            "part_unit_cost_usd": part["unit_cost_usd"],
            "supplier_id": supplier["supplier_id"],
            "supplier_name": supplier["name"],
            "supplier_tier": supplier["tier"],
            "supplier_country": supplier["country"],
            "single_source_flag": supplier["single_source"],
            "supplier_otd_rate": np.round(supplier_otd, 3),
            "supplier_defect_ppm": defect_ppm,
            "supplier_capacity_util_pct": np.round(supplier_capacity_util, 1),
            "supplier_financial_risk_score": supplier_fin_risk,
            "lead_time_variance_days": np.round(lead_time_variance_days, 1),
            "days_of_supply": days_of_supply,
            "safety_stock_threshold_days": base_safety_threshold,
            "safety_stock_ratio": safety_stock_ratio,
            "current_stock_units": current_stock_units,
            "daily_consumption_units": daily_consumption,
            "kanban_status": kanban_status,
            "corridor_id": corridor["corridor_id"],
            "transit_mode": corridor["mode"],
            "origin_location": corridor["origin"],
            "dest_location": corridor["dest"],
            "scheduled_transit_days": scheduled_transit_days,
            "actual_delay_days": actual_delay_days,
            "total_transit_days": total_projected_transit_days,
            "port_dwell_time_days": port_dwell_days,
            "weather_risk_index": weather_risk_index,
            "carrier_reliability_score": carrier_reliability,
            "disruption_risk_score": np.round(disruption_prob * 100, 1),
            "disruption_occurred": disruption_occurred,
            "disruption_severity": disruption_severity,
            "days_to_line_stoppage": days_to_line_stoppage,
            "projected_downtime_hours": projected_downtime_hours,
            "estimated_financial_loss_usd": financial_loss_usd,
            "recommended_mitigation_action": recommended_action
        }
        records.append(record)
        
    df = pd.DataFrame(records)
    csv_path = os.path.join(output_dir, "toyota_supply_chain_telemetry.csv")
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df):,} supply chain telemetry records saved to {csv_path}")
    
    # Save plants summary
    plants_df = pd.DataFrame(PLANTS)
    plants_df.to_csv(os.path.join(output_dir, "toyota_plants_directory.csv"), index=False)
    
    # Save suppliers summary
    suppliers_df = pd.DataFrame(SUPPLIERS)
    suppliers_df.to_csv(os.path.join(output_dir, "toyota_suppliers_directory.csv"), index=False)
    
    return df

if __name__ == "__main__":
    generate_supply_chain_dataset(15000)

