def build_context(metrics, incident):
    return f"""
You are a Cloud Site Reliability Engineer AI.

An incident has been detected in the system.

System Metrics:
- Error Count: {metrics['error_count']}

Incident Details:
- Type: {incident['type']}
- Severity: {incident['severity']}

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