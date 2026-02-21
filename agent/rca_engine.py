import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODELS = ["phi3", "tinyllama"]  # try in order; fallback to smaller if OOM


def _call_ollama(model: str, prompt: str) -> dict:
    """Send a chat request to Ollama and return the parsed JSON response."""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert cloud incident analyst. "
                        "Always reply with ONLY a JSON object (no markdown, no extra text) "
                        "containing exactly these keys: "
                        '"root_cause", "reasoning", "confidence", "recommended_action". '
                        '"confidence" must be a float between 0 and 1.'
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 400,
            },
        },
        timeout=180,
    )
    response.raise_for_status()
    raw_output = response.json()["message"]["content"]
    return parse_llm_json(raw_output)


def run_rca(prompt):
    """Try each model in MODELS list; return first successful result."""
    last_error = None
    for model in MODELS:
        try:
            result = _call_ollama(model, prompt)
            result["_model_used"] = model
            return result
        except Exception as e:
            last_error = e
            continue  # try next model

    # All models failed
    return {
        "root_cause": "UNKNOWN",
        "reasoning": str(last_error),
        "confidence": 0.0,
        "recommended_action": "Manual investigation required",
    }


def parse_llm_json(text):
    import re
    text = text.strip()

    # Remove markdown fences
    if "```" in text:
        text = text.replace("```json", "").replace("```", "").strip()

    # Try strict JSON parse first
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            parsed = json.loads(text[start:end])
            required = ["root_cause", "reasoning", "confidence", "recommended_action"]
            if all(k in parsed for k in required):
                return parsed
        except json.JSONDecodeError:
            pass

    # Fallback: extract meaning from free-text response
    lines = text.replace("\n\n", "\n").strip()

    # Try to find a root cause sentence
    root_match = re.search(
        r"root\s*cause[:\s]+(.+?)(?:\n|$)", lines, re.IGNORECASE
    )
    root_cause = root_match.group(1).strip().rstrip(".") if root_match else lines.split("\n")[0][:150]

    # Try to find reasoning
    reason_match = re.search(
        r"reason(?:ing)?[:\s]+(.+?)(?:\n|$)", lines, re.IGNORECASE
    )
    reasoning = reason_match.group(1).strip() if reason_match else lines[:300]

    # Try to find recommended action
    action_match = re.search(
        r"(?:recommend|action|remediat)[:\s]+(.+?)(?:\n|$)", lines, re.IGNORECASE
    )
    action = action_match.group(1).strip() if action_match else "Investigate and remediate the incident"

    # Try to find confidence
    conf_match = re.search(r"confidence[:\s]*([\d.]+)", lines, re.IGNORECASE)
    confidence = min(float(conf_match.group(1)), 1.0) if conf_match else 0.65

    return {
        "root_cause": root_cause[:200],
        "reasoning": reasoning[:400],
        "confidence": confidence,
        "recommended_action": action[:200],
    }