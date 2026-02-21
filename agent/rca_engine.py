import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"


def run_rca(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "phi3",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 300
                }
            },
            timeout=180  # Increased timeout for cold start
        )

        response.raise_for_status()

        raw_output = response.json()["message"]["content"]

        return parse_llm_json(raw_output)

    except Exception as e:
        return {
            "root_cause": "UNKNOWN",
            "reasoning": str(e),
            "confidence": 0.0,
            "recommended_action": "Manual investigation required"
        }


def parse_llm_json(text):
    try:
        text = text.strip()

        # Remove markdown if present
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == -1:
            raise ValueError("No JSON found")

        json_str = text[start:end]

        parsed = json.loads(json_str)

        required_keys = [
            "root_cause",
            "reasoning",
            "confidence",
            "recommended_action"
        ]

        for key in required_keys:
            if key not in parsed:
                raise ValueError(f"Missing key: {key}")

        return parsed

    except Exception:
        return {
            "root_cause": "PARSE_ERROR",
            "reasoning": text[:300],
            "confidence": 0.2,
            "recommended_action": "Fallback remediation"
        }