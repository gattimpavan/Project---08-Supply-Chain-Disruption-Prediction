"""
Toyota Motor Corporation - Supply Chain Disruption Prediction Web Application
Project - 08: Supply Chain Disruption Prediction

Flask Web Application & REST API serving:
- Obsidian Dark Glassmorphic Executive Dashboard
- Real-time Quad-Stream Telemetry (Supplier, Inventory, Transit, Plant)
- Machine Learning Early Warning Horizon & Feature Attribution Visuals
- Interactive What-If Counterfactual Scenario Simulator
- Autonomous Operations Protocol Dispatch Engine
- Direct Publication-Grade Executive PDF Report Download
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request, send_file

base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from data.data_generator import generate_supply_chain_dataset
from models.supply_chain_analyzer import SupplyChainAnalyzer
from models.mitigation_engine import MitigationEngine
from models.simulation_engine import SimulationEngine
from report.generate_pdf_report import build_pdf_report

app = Flask(__name__, static_folder="static", template_folder="templates")

DATA_DIR = os.path.join(base_dir, "data")
CSV_PATH = os.path.join(DATA_DIR, "toyota_supply_chain_telemetry.csv")
REPORT_PATH = os.path.join(base_dir, "report", "Toyota_Supply_Chain_Disruption_Prediction_Report.pdf")

# Generate dataset if not present
if not os.path.exists(CSV_PATH):
    print("Generating Toyota supply chain telemetry dataset (15,000 records)...")
    generate_supply_chain_dataset(num_records=15000, output_dir=DATA_DIR)

print("Initializing Supply Chain Predictive Analyzer & Training ML Models...")
analyzer = SupplyChainAnalyzer(CSV_PATH)
ml_metrics = analyzer.train_ml_models()
engine = MitigationEngine(analyzer.df)
sim = SimulationEngine(analyzer.df, reg_model=analyzer.reg_model, feature_names=analyzer.feature_names)

# Ensure publication PDF exists
if not os.path.exists(REPORT_PATH):
    print("Compiling publication-grade executive PDF report...")
    build_pdf_report(analyzer, engine, sim, REPORT_PATH)

# =====================================================================
# ROUTES & REST APIS
# =====================================================================

@app.route("/")
def index():
    """Renders the executive glassmorphic operations dashboard."""
    return render_template("index.html")

@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Toyota AI Operations & Supply Chain Disruption Intelligence",
        "version": "2.4.0",
        "records_monitored": len(analyzer.df),
        "plants_active": 6,
        "suppliers_active": 18
    })

@app.route("/api/kpis")
def get_kpis():
    """Returns top-level enterprise KPIs and ML accuracy scores."""
    kpis = analyzer.get_enterprise_kpis()
    roi = engine.calculate_enterprise_roi()
    early = analyzer.get_early_warning_horizon_stats()
    return jsonify({
        "kpis": kpis,
        "roi": roi,
        "early_warning": early,
        "ml_metrics": {
            "accuracy": analyzer.ml_metrics["classifier_accuracy"],
            "roc_auc": analyzer.ml_metrics["classifier_roc_auc"],
            "f1_score": analyzer.ml_metrics["classifier_f1"],
            "regression_r2": analyzer.ml_metrics["regression_r2"],
            "mae_hours": analyzer.ml_metrics["regression_mae_hours"]
        }
    })

@app.route("/api/plants")
def get_plants():
    """Returns plant vulnerability profiles and financial exposure."""
    return jsonify(analyzer.get_plant_vulnerability_profile())

@app.route("/api/categories")
def get_categories():
    """Returns part category failure rates and financial exposure."""
    return jsonify(analyzer.get_category_risk_breakdown())

@app.route("/api/suppliers")
def get_suppliers():
    """Returns top suppliers risk matrix."""
    return jsonify(analyzer.get_supplier_risk_matrix())

@app.route("/api/alerts")
def get_alerts():
    """Returns high-risk active disruption alerts."""
    limit = request.args.get("limit", default=20, type=int)
    alerts = engine.get_urgent_mitigation_queue(top_n=limit)
    return jsonify(alerts)

@app.route("/api/protocols")
def get_protocols():
    """Returns prescriptive mitigation protocols."""
    return jsonify(engine.evaluate_mitigation_protocols())

@app.route("/api/features")
def get_features():
    """Returns feature importance ranking."""
    return jsonify(analyzer.ml_metrics["feature_importance"])

@app.route("/api/simulate", methods=["POST", "GET"])
def simulate():
    """Executes counterfactual What-If scenario simulation."""
    if request.method == "POST":
        data = request.get_json() or {}
        port_dwell = float(data.get("port_dwell_additional_days", 0.0))
        capacity_drop = float(data.get("supplier_capacity_drop_pct", 0.0))
        weather_mult = float(data.get("weather_severity_multiplier", 1.0))
        buffer_strat = str(data.get("buffer_strategy", "dynamic_ai"))
        mitigation_active = bool(data.get("mitigation_active", True))
    else:
        port_dwell = request.args.get("port_dwell_additional_days", default=0.0, type=float)
        capacity_drop = request.args.get("supplier_capacity_drop_pct", default=0.0, type=float)
        weather_mult = request.args.get("weather_severity_multiplier", default=1.0, type=float)
        buffer_strat = request.args.get("buffer_strategy", default="dynamic_ai", type=str)
        mitigation_active = request.args.get("mitigation_active", default="true").lower() == "true"

    result = sim.simulate_scenario(
        port_dwell_additional_days=port_dwell,
        supplier_capacity_drop_pct=capacity_drop,
        weather_severity_multiplier=weather_mult,
        buffer_strategy=buffer_strat,
        mitigation_active=mitigation_active
    )
    return jsonify(result)

@app.route("/api/dispatch-mitigation", methods=["POST"])
def dispatch_mitigation():
    """Simulates autonomous dispatch of a prescriptive mitigation protocol."""
    data = request.get_json() or {}
    record_id = data.get("record_id", "TYT-SC-100000")
    protocol_id = data.get("protocol_id", "PROT-ALPHA")
    
    return jsonify({
        "status": "DISPATCHED",
        "record_id": record_id,
        "protocol_id": protocol_id,
        "message": f"Autonomous Operations Protocol {protocol_id} successfully executed for Shipment {record_id}.",
        "audit_timestamp": pd.Timestamp.now().isoformat(),
        "prevention_success": True
    })

@app.route("/download-report")
def download_report():
    """Streams publication-grade PDF report."""
    if not os.path.exists(REPORT_PATH):
        build_pdf_report(analyzer, engine, sim, REPORT_PATH)
    return send_file(
        REPORT_PATH,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="Toyota_Supply_Chain_Disruption_Prediction_Report.pdf"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5008))
    print(f"\n==========================================================================")
    print(f" Toyota AI Operations & Supply Chain Disruption System running at:")
    print(f" >>> http://localhost:{port} <<<")
    print(f"==========================================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)

