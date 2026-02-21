"""
Autonomous Cloud Incident System — Main Loop (Full Pipeline)

Continuously monitors the microservice, detects incidents using both
threshold and statistical anomaly detection, runs AI root cause analysis,
calculates risk scores, orchestrates remediation via n8n + fallback,
generates reports, and exposes state for the Streamlit dashboard.

Pipeline: Fetch Metrics -> Anomaly Detection -> Incident Detection ->
          AI RCA -> Risk Scoring -> n8n Remediation -> Verify -> Report
"""

import sys
import os
import time
import threading
from datetime import datetime

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.cloud_connector import fetch_metrics
from agent.detector import detect_incidents, detect_incident
from agent.anomaly_engine import (
    detect_anomalies, ingest_metrics, get_stats,
    get_anomaly_log, get_metric_history, get_metric_timestamps,
)
from agent.context_builder import build_context
from agent.rca_engine import run_rca
from agent.risk_engine import calculate_risk_score
from agent.remediation_engine import orchestrate_remediation, get_remediation_log
from agent.report_generator import (
    generate_incident_report,
    append_to_log,
    save_report_json,
    generate_summary,
)
from agent.knowledge_base import get_common_causes
from agent.remediation_trigger import verify_service_health

# ── Configuration ──
POLL_INTERVAL = 10          # seconds between detection scans
COOLDOWN = 30               # seconds to wait after a remediation cycle

# ── Shared state for dashboard ──
_dashboard_state = {
    "status": "starting",
    "last_poll": None,
    "current_metrics": {},
    "last_health": {},
    "active_incidents": [],
    "last_rca_results": {},
    "last_risk_assessments": [],
    "last_anomalies": [],
    "incident_reports": [],
    "summary": {},
    "loop_count": 0,
    "started_at": datetime.now().isoformat(),
}
_state_lock = threading.Lock()


def get_dashboard_state() -> dict:
    """Thread-safe read of current pipeline state for the dashboard."""
    with _state_lock:
        return dict(_dashboard_state)


def _update_state(**kwargs):
    """Thread-safe update of dashboard state."""
    with _state_lock:
        _dashboard_state.update(kwargs)


def log(msg: str):
    """Timestamped log output."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def main_loop():
    """
    Full autonomous pipeline:
      1. Fetch metrics
      2. Statistical anomaly detection
      3. Threshold + health-based incident detection
      4. AI Root Cause Analysis (Ollama phi3)
      5. Risk scoring
      6. Remediation via n8n + fallback
      7. Post-remediation verification
      8. Report generation
    """
    log("=" * 60)
    log("  Autonomous Cloud Incident System — FULL PIPELINE")
    log(f"  Poll interval: {POLL_INTERVAL}s | Cooldown: {COOLDOWN}s")
    log("=" * 60)

    _update_state(status="running")

    while True:
        try:
            _update_state(
                last_poll=datetime.now().isoformat(),
                loop_count=_dashboard_state["loop_count"] + 1,
            )

            # ── PHASE 1: Fetch Metrics ──
            log("Fetching metrics...")
            metrics = fetch_metrics()
            _update_state(current_metrics=metrics)
            log(f"   CPU={metrics.get('cpu_percent', 0)}% | "
                f"MEM={metrics.get('memory_percent', 0)}% | "
                f"Errors={metrics.get('error_count', 0)}")

            # ── PHASE 2: Anomaly Detection (Statistical) ──
            anomalies = detect_anomalies(metrics)
            _update_state(last_anomalies=anomalies)
            if anomalies:
                for a in anomalies:
                    log(f"   Anomaly: {a['metric']} z={a['z_score']} ({a['direction']})")

            # ── PHASE 3: Incident Detection ──
            incidents = detect_incidents()

            # Also use simple error-count trend detection
            simple_inc = detect_incident(metrics)
            if simple_inc and not any(i["type"] == simple_inc["type"] for i in incidents):
                incidents.append(simple_inc)

            # Check health for dashboard
            health = verify_service_health()
            _update_state(last_health=health, active_incidents=incidents)

            if not incidents:
                log("No incidents — system healthy")
                _update_state(status="healthy")
                time.sleep(POLL_INTERVAL)
                continue

            _update_state(status="incident_detected")

            # ── PHASE 4: AI RCA + Risk Scoring for each incident ──
            rca_results = {}
            risk_assessments = []
            reports = []

            for incident in incidents:
                inc_type = incident["type"]
                details = incident.get("details", {})
                log(f"INCIDENT: {inc_type}")
                log(f"   Details: {details}")
                log(f"   Known causes: {get_common_causes(inc_type)[:2]}")

                # AI Root Cause Analysis
                rca = None
                try:
                    prompt = build_context(metrics, incident)
                    rca = run_rca(prompt)
                    rca_results[inc_type] = rca
                    log(f"   AI RCA: {rca.get('root_cause', 'UNKNOWN')} "
                        f"(confidence={rca.get('confidence', 0)})")
                    log(f"   Recommended: {rca.get('recommended_action', 'N/A')}")
                except Exception as e:
                    log(f"   AI RCA failed: {e}")

                # Risk scoring
                risk = calculate_risk_score(inc_type, metrics, rca, anomalies)
                risk_assessments.append(risk)
                log(f"   Risk: {risk['risk_score']} ({risk['risk_level']})")

                # ── PHASE 5: Remediation ──
                _update_state(status="remediating")
                log(f"   Orchestrating remediation for {inc_type}...")
                rem_result = orchestrate_remediation(
                    inc_type, details, risk["risk_score"]
                )
                log(f"   Remediation: {rem_result['status']} "
                    f"(attempt #{rem_result['attempt']}, {rem_result['elapsed_s']}s)")

                # ── PHASE 6: Report Generation ──
                report = generate_incident_report(
                    incident=incident,
                    metrics=metrics,
                    rca_result=rca,
                    risk_assessment=risk,
                    remediation_result=rem_result,
                    anomalies=anomalies,
                )
                reports.append(report)
                append_to_log(report)
                save_report_json(report)
                log(f"   Report: {report['report_id']} ({report['status']})")

            # Update dashboard state with all results
            _update_state(
                last_rca_results=rca_results,
                last_risk_assessments=risk_assessments,
                incident_reports=_dashboard_state["incident_reports"] + reports,
                summary=generate_summary(
                    _dashboard_state["incident_reports"] + reports
                ),
            )

            # Final verification
            final_health = verify_service_health()
            if final_health.get("status") == "healthy":
                log("REMEDIATION COMPLETE — service restored")
                _update_state(status="recovered")
            else:
                log("Service still degraded — check dashboard for details")
                _update_state(status="degraded")

            # Cooldown
            log(f"Cooldown {COOLDOWN}s...")
            time.sleep(COOLDOWN)

        except KeyboardInterrupt:
            log("Shutting down (Ctrl+C)")
            _update_state(status="stopped")
            break
        except Exception as e:
            log(f"Error in main loop: {e}")
            _update_state(status="error")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main_loop()
