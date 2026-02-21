"""
Remediation Trigger — Sends detected incidents to n8n production webhook.

Usage:
    from agent.remediation_trigger import trigger_remediation
    result = trigger_remediation("MEMORY_LEAK")
"""

import requests
import time
from datetime import datetime

# ── n8n Production Webhook (NOT /webhook-test) ──
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/remediation"

# Service base URL
SERVICE_URL = "http://127.0.0.1:8000"


def trigger_remediation(incident_type: str, details: dict | None = None) -> dict:
    """
    Send an incident to the n8n production webhook for automated remediation.

    Args:
        incident_type: One of MEMORY_LEAK, DB_OVERLOAD, CRASH, CPU_SPIKE, LATENCY_SPIKE
        details: Optional dict with extra context (cpu_percent, memory_percent, etc.)

    Returns:
        dict with status, response, and timing info
    """
    payload = {
        "incident_type": incident_type,
        "timestamp": datetime.now().isoformat(),
        "source": "python-detection-agent",
        "details": details or {},
    }

    print(f"[TRIGGER] Sending {incident_type} to n8n webhook: {N8N_WEBHOOK_URL}")
    start = time.time()

    try:
        resp = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=30,
        )
        elapsed = round(time.time() - start, 2)

        if resp.status_code == 200:
            print(f"[TRIGGER] ✅ n8n accepted remediation for {incident_type} ({elapsed}s)")
            # n8n may return JSON, plain text, or empty body
            try:
                n8n_resp = resp.json()
            except Exception:
                n8n_resp = resp.text or "OK"
            return {
                "status": "success",
                "incident_type": incident_type,
                "n8n_response": n8n_resp,
                "elapsed_s": elapsed,
            }
        else:
            print(f"[TRIGGER] ⚠️ n8n returned {resp.status_code}: {resp.text}")
            return {
                "status": "error",
                "incident_type": incident_type,
                "http_status": resp.status_code,
                "response": resp.text,
                "elapsed_s": elapsed,
            }

    except requests.ConnectionError:
        print(f"[TRIGGER] ❌ Cannot reach n8n at {N8N_WEBHOOK_URL}. Is it running?")
        return {"status": "connection_error", "incident_type": incident_type}
    except requests.Timeout:
        print(f"[TRIGGER] ❌ n8n webhook timed out after 30s")
        return {"status": "timeout", "incident_type": incident_type}
    except Exception as e:
        print(f"[TRIGGER] ❌ Unexpected error: {e}")
        return {"status": "error", "incident_type": incident_type, "error": str(e)}


def verify_service_health() -> dict:
    """
    Check if the service has recovered after remediation.

    Returns:
        dict with health status and active incidents
    """
    try:
        resp = requests.get(f"{SERVICE_URL}/health", timeout=5)
        data = resp.json()
        status = data.get("status", "unknown")
        incidents = data.get("active_incidents", [])

        if status == "healthy":
            print(f"[VERIFY] ✅ Service is HEALTHY — no active incidents")
        else:
            print(f"[VERIFY] ⚠️ Service is {status.upper()} — active: {incidents}")

        return data

    except requests.ConnectionError:
        print(f"[VERIFY] ❌ Service unreachable at {SERVICE_URL}")
        return {"status": "unreachable", "active_incidents": []}
    except Exception as e:
        print(f"[VERIFY] ❌ Error checking health: {e}")
        return {"status": "error", "active_incidents": [], "error": str(e)}


# ── Direct test ──
if __name__ == "__main__":
    print("=== Testing remediation trigger ===\n")

    # Test 1: Trigger a memory leak remediation
    result = trigger_remediation("MEMORY_LEAK", {"memory_percent": 92.5})
    print(f"Result: {result}\n")

    # Test 2: Verify health
    health = verify_service_health()
    print(f"Health: {health}\n")
