"""
Remediation Engine — Orchestrates the full remediation lifecycle.

Coordinates: n8n webhook trigger → verify → fallback direct remediation → verify.
Tracks remediation attempts and enforces escalation rules.
"""

import time
import requests
from datetime import datetime

from agent.knowledge_base import (
    get_remediation_endpoint,
    get_remediation_steps,
    get_escalation_rules,
    get_expected_recovery_time,
)
from agent.remediation_trigger import trigger_remediation, verify_service_health

SERVICE_URL = "http://127.0.0.1:8000"

# Track remediation history for escalation
_remediation_log: list[dict] = []
_attempt_counts: dict[str, int] = {}


def orchestrate_remediation(
    incident_type: str,
    details: dict | None = None,
    risk_score: float = 0.5,
) -> dict:
    """
    Full remediation lifecycle for an incident.

    1. Send to n8n webhook
    2. Wait for expected recovery time
    3. Verify health
    4. If still degraded → direct fallback remediation
    5. Verify again
    6. Track attempts and check escalation rules

    Returns a result dict with status, actions taken, and timing.
    """
    start = time.time()
    actions = []
    escalation = get_escalation_rules()
    max_attempts = escalation.get("max_auto_remediation_attempts", 3)

    # Track attempts
    count = _attempt_counts.get(incident_type, 0) + 1
    _attempt_counts[incident_type] = count

    if count > max_attempts:
        result = {
            "status": "escalated",
            "incident_type": incident_type,
            "message": f"Max auto-remediation attempts ({max_attempts}) exceeded. Escalating.",
            "attempt": count,
            "actions": [],
            "elapsed_s": 0,
            "timestamp": datetime.now().isoformat(),
        }
        _remediation_log.append(result)
        return result

    # Step 1: n8n webhook
    n8n_result = trigger_remediation(incident_type, details)
    actions.append({
        "action": "n8n_webhook",
        "result": n8n_result.get("status", "unknown"),
        "detail": n8n_result,
    })

    # Step 2: Wait for expected recovery
    recovery_time = get_expected_recovery_time(incident_type)
    time.sleep(min(recovery_time, 10))  # Cap at 10s wait

    # Step 3: Verify health
    health = verify_service_health()
    status = health.get("status", "unknown")
    active = health.get("active_incidents", [])
    actions.append({
        "action": "verify_after_n8n",
        "status": status,
        "active_incidents": active,
    })

    if status == "healthy" and not active:
        # Reset attempt count on success
        _attempt_counts[incident_type] = 0
        result = _build_result("resolved_by_n8n", incident_type, count, actions, start)
        _remediation_log.append(result)
        return result

    # Step 4: Fallback — direct endpoint call
    endpoint = get_remediation_endpoint(incident_type)
    if endpoint:
        fallback_result = _call_endpoint(endpoint)
        actions.append({
            "action": "direct_fallback",
            "endpoint": endpoint,
            "result": fallback_result,
        })
    else:
        # No specific endpoint — try /restart
        fallback_result = _call_endpoint("/restart")
        actions.append({
            "action": "direct_fallback_restart",
            "endpoint": "/restart",
            "result": fallback_result,
        })

    # Step 5: Verify again
    time.sleep(3)
    health2 = verify_service_health()
    status2 = health2.get("status", "unknown")
    active2 = health2.get("active_incidents", [])
    actions.append({
        "action": "verify_after_fallback",
        "status": status2,
        "active_incidents": active2,
    })

    if status2 == "healthy" and not active2:
        _attempt_counts[incident_type] = 0
        result = _build_result("resolved_by_fallback", incident_type, count, actions, start)
        _remediation_log.append(result)
        return result

    # Still not resolved
    final_status = "unresolved"
    if count >= escalation.get("escalation_after_failures", 2):
        final_status = "needs_escalation"

    result = _build_result(final_status, incident_type, count, actions, start)
    _remediation_log.append(result)
    return result


def _call_endpoint(path: str) -> dict:
    """Call a service remediation endpoint."""
    url = f"{SERVICE_URL}{path}" if path.startswith("/") else path
    try:
        resp = requests.post(url, timeout=10)
        if resp.status_code == 200:
            return {"success": True, "response": resp.json()}
        return {"success": False, "status_code": resp.status_code}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _build_result(
    status: str,
    incident_type: str,
    attempt: int,
    actions: list,
    start_time: float,
) -> dict:
    """Build a standardized remediation result dict."""
    return {
        "status": status,
        "incident_type": incident_type,
        "attempt": attempt,
        "actions": actions,
        "elapsed_s": round(time.time() - start_time, 2),
        "timestamp": datetime.now().isoformat(),
    }


def get_remediation_log() -> list[dict]:
    """Return the full remediation history."""
    return list(_remediation_log)


def get_attempt_count(incident_type: str) -> int:
    """Return the current attempt count for an incident type."""
    return _attempt_counts.get(incident_type, 0)


def reset_attempts(incident_type: str | None = None):
    """Reset attempt counters. If incident_type is None, resets all."""
    if incident_type:
        _attempt_counts.pop(incident_type, None)
    else:
        _attempt_counts.clear()


def get_recommended_steps(incident_type: str) -> list[str]:
    """Return knowledge-base remediation steps for an incident type."""
    return get_remediation_steps(incident_type)
