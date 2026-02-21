def build_context(metrics, incident):
    return f"""
You are a senior Site Reliability Engineer AI.

System Metrics:
- Error Count: {metrics.get('error_count', 0)}

Incident:
- Type: {incident.get('type')}
- Severity: {incident.get('severity')}

Think step-by-step internally, but return ONLY valid JSON:

{{
  "root_cause": "...",
  "confidence": "LOW | MEDIUM | HIGH",
  "recommended_action": "...",
  "justification": "1-2 sentence technical reasoning"
}}

Return ONLY raw JSON.
No markdown.
"""