"""
Context Builder — Builds an AI prompt from metrics and incident data.
"""


def build_context(metrics: dict, incident: dict) -> str:
    """
    Build a structured prompt for the RCA engine.

    Works with both simple incidents (severity field) and
    rich incidents (details dict) from detect_incidents().
    """
    severity = incident.get("severity", "UNKNOWN")
    details = incident.get("details", {})
    error_count = metrics.get("error_count", 0)
    cpu = metrics.get("cpu_percent", "N/A")
    mem = metrics.get("memory_percent", "N/A")

    return (
        f"You are a Cloud SRE AI. A {incident['type']} incident (severity={severity}) "
        f"occurred. System: CPU={cpu}%, Memory={mem}%, Errors={error_count}. "
        f"Details: {details}. "
        f"Analyze the root cause and reply with ONLY valid JSON: "
        f'{{"root_cause":"...","reasoning":"...","confidence":0.0,"recommended_action":"..."}}'
    )