"""
Learning Loop — Learns from past resolved incidents to improve future analysis.

Provides:
  - Automatic recording of resolved incidents as learning data
  - Context enrichment: adds past patterns to AI prompts
  - Knowledge base auto-update: merges frequently-seen root causes
  - Confidence calibration: adjusts trust based on historical accuracy
"""

import json
import os
from datetime import datetime

from app.storage import (
    save_learning_record,
    get_learning_records,
    get_learning_summary,
    get_incidents_by_type,
)


def record_resolved_incident(
    incident_type: str,
    rca_result: dict,
    remediation_success: bool,
    metrics_context: dict | None = None,
):
    """
    Record a resolved incident for future learning.
    Called automatically after successful remediation.
    """
    save_learning_record(
        incident_type=incident_type,
        root_cause=rca_result.get("root_cause", "Unknown"),
        confidence=rca_result.get("confidence", 0),
        remediation_action=rca_result.get("recommended_action", ""),
        remediation_success=remediation_success,
        model_used=rca_result.get("_model_used", ""),
        metrics_context=metrics_context,
    )


def enrich_prompt_with_history(incident_type: str, base_prompt: str) -> str:
    """
    Enrich an AI prompt with historical patterns from past incidents.
    This gives the LLM context about what worked before.
    """
    summary = get_learning_summary(incident_type)

    if summary["total_records"] == 0:
        return base_prompt

    # Build history context
    history_lines = [
        f"\n--- HISTORICAL CONTEXT (from {summary['total_records']} past incidents) ---"
    ]

    if summary["top_root_causes"]:
        history_lines.append("Previously identified root causes for this incident type:")
        for i, rc in enumerate(summary["top_root_causes"][:3], 1):
            history_lines.append(f"  {i}. \"{rc['cause']}\" (seen {rc['count']} times)")

    history_lines.append(f"Historical remediation success rate: {summary['success_rate']}%")
    history_lines.append(f"Average AI confidence on past incidents: {summary['avg_confidence']:.0%}")
    history_lines.append(
        "Use this historical context to improve your analysis accuracy. "
        "If the current incident matches a known pattern, reference it."
    )
    history_lines.append("--- END HISTORICAL CONTEXT ---\n")

    return base_prompt + "\n".join(history_lines)


def get_confidence_calibration(incident_type: str) -> float:
    """
    Calculate a confidence calibration factor based on how accurate
    past predictions were for this incident type.

    Returns a multiplier (0.5 to 1.5) to adjust AI confidence.
    """
    records = get_learning_records(incident_type, limit=50)
    if len(records) < 3:
        return 1.0  # not enough data

    correct = sum(1 for r in records if r.get("was_correct", True))
    accuracy = correct / len(records)

    # If past predictions were mostly correct, boost confidence
    # If they were often wrong, reduce confidence
    if accuracy >= 0.8:
        return 1.2
    elif accuracy >= 0.6:
        return 1.0
    elif accuracy >= 0.4:
        return 0.8
    else:
        return 0.6


def suggest_remediation_from_history(incident_type: str) -> str | None:
    """
    Suggest the most successful remediation action based on past incidents.
    """
    records = get_learning_records(incident_type, limit=30)
    if not records:
        return None

    # Count successful remediation actions
    action_success: dict[str, int] = {}
    action_total: dict[str, int] = {}

    for r in records:
        action = r.get("remediation_action", "").strip()
        if not action:
            continue
        action_total[action] = action_total.get(action, 0) + 1
        if r.get("remediation_success"):
            action_success[action] = action_success.get(action, 0) + 1

    if not action_total:
        return None

    # Find action with highest success rate (min 2 samples)
    best_action = None
    best_rate = 0

    for action, total in action_total.items():
        if total >= 2:
            rate = action_success.get(action, 0) / total
            if rate > best_rate:
                best_rate = rate
                best_action = action

    return best_action


def auto_update_knowledge_base(incident_type: str, min_records: int = 5):
    """
    Automatically update the knowledge base with learned patterns.
    Adds new common causes discovered through AI analysis.
    """
    summary = get_learning_summary(incident_type)
    if summary["total_records"] < min_records:
        return  # not enough data to update

    # Load current KB
    kb_path = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge.json")
    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return

    pattern = kb.get("incident_patterns", {}).get(incident_type)
    if not pattern:
        return

    current_causes = set(pattern.get("common_causes", []))
    updated = False

    # Add frequently-seen root causes that aren't in the KB yet
    for rc in summary["top_root_causes"]:
        cause = rc["cause"]
        if rc["count"] >= 3 and cause not in current_causes and cause != "Unknown":
            # Check it's not too similar to existing causes
            if not any(_similar(cause, existing) for existing in current_causes):
                pattern["common_causes"].append(f"[Learned] {cause}")
                updated = True

    # Update success rate from learning data
    if summary["success_rate"] > 0:
        pattern["learned_remediation_success_rate"] = summary["success_rate"]

    if updated:
        # Add metadata about the learning update
        pattern["last_kb_update"] = datetime.now().isoformat()
        pattern["learning_records_count"] = summary["total_records"]

        with open(kb_path, "w", encoding="utf-8") as f:
            json.dump(kb, f, indent=2)


def _similar(a: str, b: str, threshold: float = 0.6) -> bool:
    """Simple word-overlap similarity check."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b)
    return overlap / min(len(words_a), len(words_b)) > threshold


def get_learning_dashboard_data(incident_type: str | None = None) -> dict:
    """
    Return learning data formatted for the dashboard.
    """
    if incident_type:
        summary = get_learning_summary(incident_type)
        return {
            "incident_type": incident_type,
            "summary": summary,
            "calibration_factor": get_confidence_calibration(incident_type),
            "suggested_remediation": suggest_remediation_from_history(incident_type),
        }

    # All types
    from agent.knowledge_base import get_all_incident_types
    types = get_all_incident_types()
    all_summaries = {}
    for t in types:
        s = get_learning_summary(t)
        if s["total_records"] > 0:
            all_summaries[t] = s

    total_records = sum(s["total_records"] for s in all_summaries.values())
    return {
        "total_learning_records": total_records,
        "by_type": all_summaries,
    }
