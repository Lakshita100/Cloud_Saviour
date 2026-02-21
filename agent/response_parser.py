import json
import re

def parse_llm_response(response_text):
    try:
        cleaned = re.sub(r"```json|```", "", response_text).strip()

        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found")

        parsed = json.loads(json_match.group())

        return {
            "root_cause": parsed.get("root_cause", "Unknown"),
            "confidence": parsed.get("confidence", "LOW"),
            "recommended_action": parsed.get("recommended_action", "Manual inspection required"),
            "justification": parsed.get("justification", "No reasoning provided")
        }

    except Exception as e:
        print("⚠️ Parsing error:", e)
        return {
            "root_cause": "LLM output invalid",
            "confidence": "LOW",
            "recommended_action": "Fallback: restart service",
            "justification": "Parsing failure fallback triggered"
        }