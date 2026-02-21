import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def run_rca(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "phi3",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=60   # 🔥 ADD THIS
        )

        response.raise_for_status()
        return response.json().get("response", "")

    except requests.exceptions.Timeout:
        print("❌ Ollama request timed out")
        return ""

    except Exception as e:
        print("❌ Error:", e)
        return ""