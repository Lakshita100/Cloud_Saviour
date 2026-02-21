"""
Risk Engine — Calculates risk scores for incidents.

Combines multiple signals: knowledge base weight, AI confidence,
metric severity, and anomaly z-scores into a composite risk score.
"""

from datetime import datetime
from agent.knowledge_base import get_risk_weight, get_severity, get_risk_thresholds


def calculate_risk_score(
    incident_type: str,
    metrics: dict,
    rca_result: dict | None = None,
    anomalies: list[dict] | None = None,
) -> dict:
    """
    Calculate a composite risk score (0.0 – 1.0) for an incident.

    Factors:
      - Knowledge base weight (40%)
      - AI RCA confidence (25%)
      - Metric severity level (20%)
      - Anomaly z-score magnitude (15%)

    Returns dict with score, level, breakdown, and timestamp.
    """
    # 1. Knowledge base weight (0-1)
    kb_weight = get_risk_weight(incident_type)

    # 2. AI confidence (invert: low confidence = higher risk)
    ai_confidence = 0.5
    if rca_result:
        raw_conf = rca_result.get("confidence", 0.5)
        # If AI is very confident, risk is well-understood (slightly lower)
        # If AI is uncertain, risk is unknown (higher)
        ai_confidence = 1.0 - (raw_conf * 0.5)  # Maps 0→1.0, 1→0.5

    # 3. Severity level from knowledge base
    severity = get_severity(incident_type, metrics)
    severity_scores = {"low": 0.2, "medium": 0.5, "high": 0.75, "critical": 1.0}
    sev_score = severity_scores.get(severity, 0.5)

    # 4. Anomaly z-score magnitude (normalized)
    anomaly_score = 0.0
    if anomalies:
        max_z = max(abs(a.get("z_score", 0)) for a in anomalies)
        anomaly_score = min(max_z / 5.0, 1.0)  # Normalize: z=5 → 1.0

    # Weighted composite
    composite = (
        kb_weight * 0.40
        + ai_confidence * 0.25
        + sev_score * 0.20
        + anomaly_score * 0.15
    )
    composite = round(min(composite, 1.0), 3)

    # Determine risk level
    level = _score_to_level(composite)

    return {
        "risk_score": composite,
        "risk_level": level,
        "incident_type": incident_type,
        "severity": severity,
        "breakdown": {
            "kb_weight": round(kb_weight, 3),
            "ai_uncertainty": round(ai_confidence, 3),
            "severity_score": round(sev_score, 3),
            "anomaly_score": round(anomaly_score, 3),
        },
        "timestamp": datetime.now().isoformat(),
    }


def _score_to_level(score: float) -> str:
    """Map a 0-1 score to a risk level string."""
    thresholds = get_risk_thresholds()
    for level, (low, high) in thresholds.items():
        if low <= score < high:
            return level
    return "critical" if score >= 0.8 else "medium"


def batch_risk_assessment(
    incidents: list[dict],
    metrics: dict,
    rca_results: dict | None = None,
    anomalies: list[dict] | None = None,
) -> list[dict]:
    """
    Calculate risk for multiple incidents at once.

    Args:
        incidents: List of incident dicts with 'type' key
        metrics: Current system metrics
        rca_results: Optional dict mapping incident_type → rca result
        anomalies: Optional list of anomaly dicts

    Returns list of risk assessment dicts, sorted by score descending.
    """
    assessments = []
    rca_map = rca_results or {}

    for incident in incidents:
        inc_type = incident.get("type", "UNKNOWN")
        rca = rca_map.get(inc_type)
        assessment = calculate_risk_score(inc_type, metrics, rca, anomalies)
        assessments.append(assessment)

    # Sort by risk score descending (highest risk first)
    assessments.sort(key=lambda a: a["risk_score"], reverse=True)
    return assessments
