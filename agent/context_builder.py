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

    return f"""
You are a Cloud Site Reliability Engineer AI.

An incident has been detected in the system.

System Metrics:
- Error Count: {error_count}
- CPU Usage: {cpu}%
- Memory Usage: {mem}%

Incident Details:
- Type: {incident['type']}
- Severity: {severity}
- Details: {details}

Your task:
1. Identify the most probable root cause.
2. Briefly explain your reasoning.
3. Provide a confidence score between 0 and 1.
4. Suggest a recommended remediation action.

IMPORTANT:
Respond ONLY in this exact JSON format:

{{
  "root_cause": "string",
  "reasoning": "string",
  "confidence": 0.0,
  "recommended_action": "string"
}}

Do NOT repeat the input.
Do NOT include markdown.
Return ONLY valid JSON.
"""