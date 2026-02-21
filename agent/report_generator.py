"""
Report Generator — Creates structured incident reports.

Generates reports for individual incidents and summary reports
for the dashboard, including full lifecycle tracking.
"""

import json
import os
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
LOGS_FILE = os.path.join(REPORTS_DIR, "logs.txt")


def generate_incident_report(
    incident: dict,
    metrics: dict,
    rca_result: dict | None = None,
    risk_assessment: dict | None = None,
    remediation_result: dict | None = None,
    anomalies: list[dict] | None = None,
) -> dict:
    """
    Generate a comprehensive incident report.

    Combines detection data, AI analysis, risk assessment,
    and remediation outcome into a single structured report.
    """
    report = {
        "report_id": f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "timestamp": datetime.now().isoformat(),
        "incident": {
            "type": incident.get("type", "UNKNOWN"),
            "details": incident.get("details", {}),
            "severity": incident.get("severity", "UNKNOWN"),
        },
        "metrics_snapshot": {
            "cpu_percent": metrics.get("cpu_percent", 0),
            "memory_percent": metrics.get("memory_percent", 0),
            "error_count": metrics.get("error_count", 0),
        },
        "ai_analysis": None,
        "risk_assessment": None,
        "remediation": None,
        "anomalies": [],
        "status": "open",
    }

    if rca_result:
        report["ai_analysis"] = {
            "root_cause": rca_result.get("root_cause", "UNKNOWN"),
            "reasoning": rca_result.get("reasoning", ""),
            "confidence": rca_result.get("confidence", 0),
            "recommended_action": rca_result.get("recommended_action", ""),
        }

    if risk_assessment:
        report["risk_assessment"] = {
            "risk_score": risk_assessment.get("risk_score", 0),
            "risk_level": risk_assessment.get("risk_level", "unknown"),
            "severity": risk_assessment.get("severity", "unknown"),
            "breakdown": risk_assessment.get("breakdown", {}),
        }

    if remediation_result:
        report["remediation"] = {
            "status": remediation_result.get("status", "unknown"),
            "attempt": remediation_result.get("attempt", 0),
            "elapsed_s": remediation_result.get("elapsed_s", 0),
            "actions": remediation_result.get("actions", []),
        }
        if remediation_result.get("status") in ("resolved_by_n8n", "resolved_by_fallback"):
            report["status"] = "resolved"
        elif remediation_result.get("status") == "escalated":
            report["status"] = "escalated"
        else:
            report["status"] = "unresolved"

    if anomalies:
        report["anomalies"] = [
            {
                "metric": a.get("metric", ""),
                "z_score": a.get("z_score", 0),
                "value": a.get("value", 0),
                "direction": a.get("direction", ""),
            }
            for a in anomalies
        ]

    return report


def append_to_log(report: dict):
    """Append a report summary to the logs file."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    line = (
        f"[{report['timestamp']}] "
        f"{report['incident']['type']} | "
        f"Status: {report['status']} | "
        f"Risk: {report.get('risk_assessment', {}).get('risk_level', 'N/A')} | "
        f"RCA: {report.get('ai_analysis', {}).get('root_cause', 'N/A')[:60]}"
    )
    with open(LOGS_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def save_report_json(report: dict):
    """Save a full report as a JSON file."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filepath = os.path.join(REPORTS_DIR, f"{report['report_id']}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    return filepath


def read_logs() -> list[str]:
    """Read all log lines from the logs file."""
    if not os.path.exists(LOGS_FILE):
        return []
    with open(LOGS_FILE, "r", encoding="utf-8") as f:
        return f.readlines()


def get_report_files() -> list[str]:
    """List all JSON report files in the data directory."""
    if not os.path.isdir(REPORTS_DIR):
        return []
    return [
        f for f in os.listdir(REPORTS_DIR)
        if f.startswith("INC-") and f.endswith(".json")
    ]


def load_report(report_id: str) -> dict | None:
    """Load a specific report by ID."""
    filepath = os.path.join(REPORTS_DIR, f"{report_id}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_summary(reports: list[dict]) -> dict:
    """
    Generate a summary from multiple incident reports.

    Returns counts by type, status, risk level, and average metrics.
    """
    summary = {
        "total_incidents": len(reports),
        "by_type": {},
        "by_status": {},
        "by_risk_level": {},
        "avg_risk_score": 0.0,
        "avg_confidence": 0.0,
        "generated_at": datetime.now().isoformat(),
    }

    total_risk = 0.0
    total_conf = 0.0
    risk_count = 0
    conf_count = 0

    for r in reports:
        # Count by type
        inc_type = r.get("incident", {}).get("type", "UNKNOWN")
        summary["by_type"][inc_type] = summary["by_type"].get(inc_type, 0) + 1

        # Count by status
        status = r.get("status", "unknown")
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

        # Count by risk level
        risk_level = r.get("risk_assessment", {}).get("risk_level", "unknown") if r.get("risk_assessment") else "unknown"
        summary["by_risk_level"][risk_level] = summary["by_risk_level"].get(risk_level, 0) + 1

        # Accumulate for averages
        if r.get("risk_assessment"):
            total_risk += r["risk_assessment"].get("risk_score", 0)
            risk_count += 1
        if r.get("ai_analysis"):
            total_conf += r["ai_analysis"].get("confidence", 0)
            conf_count += 1

    if risk_count > 0:
        summary["avg_risk_score"] = round(total_risk / risk_count, 3)
    if conf_count > 0:
        summary["avg_confidence"] = round(total_conf / conf_count, 3)

    return summary
