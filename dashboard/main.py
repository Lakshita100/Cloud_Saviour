<<<<<<< Updated upstream
from fastapi import FastAPI
from prometheus_client import Counter, generate_latest
from fastapi.responses import Response

app = FastAPI()

# Define metric
error_counter = Counter("app_errors_total", "Total number of application errors")

@app.get("/trigger/memory")
def trigger_memory():
    error_counter.inc()
    return {"message": "Error triggered"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")
=======
"""
Autonomous Cloud Incident System — Main Loop

Continuously monitors the microservice, detects incidents,
triggers n8n remediation, and verifies recovery.

    Detection → n8n Webhook → Remediation → Verification
"""

import sys
import os
import time
import requests
from datetime import datetime

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.detector import detect_incidents, check_health
from agent.remediation_trigger import trigger_remediation, verify_service_health

# ── Configuration ──
POLL_INTERVAL = 10          # seconds between detection scans
VERIFY_DELAY = 5            # seconds to wait before verifying remediation
MAX_VERIFY_RETRIES = 6      # max retries for verification (6 × 5s = 30s)
COOLDOWN = 30               # seconds to wait after a remediation cycle

SERVICE_URL = "http://127.0.0.1:8000"

# Map incident types → service remediation endpoints
REMEDIATION_ENDPOINTS = {
    "MEMORY_LEAK":   f"{SERVICE_URL}/remediate/memory_leak",
    "DB_OVERLOAD":   f"{SERVICE_URL}/remediate/db_overload",
    "CRASH":         f"{SERVICE_URL}/remediate/crash",
    "CPU_SPIKE":     f"{SERVICE_URL}/restart",
    "LATENCY_SPIKE": f"{SERVICE_URL}/restart",
}


def log(msg: str):
    """Timestamped log output."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def direct_remediate(incident_type: str) -> bool:
    """
    Fallback: call the service remediation endpoint directly
    if n8n didn't resolve the incident.
    """
    url = REMEDIATION_ENDPOINTS.get(incident_type)
    if not url:
        log(f"[FALLBACK] No remediation endpoint for {incident_type}")
        return False
    try:
        log(f"[FALLBACK] Calling {url} directly...")
        resp = requests.post(url, timeout=10)
        if resp.status_code == 200:
            log(f"[FALLBACK] ✅ Direct remediation succeeded for {incident_type}")
            return True
        else:
            log(f"[FALLBACK] ⚠️ Got {resp.status_code} from {url}")
            return False
    except Exception as e:
        log(f"[FALLBACK] ❌ Error: {e}")
        return False


def run_verification_loop(incident_types: list[str] | None = None) -> bool:
    """
    Poll /health up to MAX_VERIFY_RETRIES times to confirm recovery.
    If still degraded after 3 attempts, try direct fallback remediation.

    Returns True if service recovered, False if still degraded.
    """
    for attempt in range(1, MAX_VERIFY_RETRIES + 1):
        log(f"[VERIFY] Attempt {attempt}/{MAX_VERIFY_RETRIES} ...")
        time.sleep(VERIFY_DELAY)

        health = verify_service_health()
        status = health.get("status", "unknown")
        active = health.get("active_incidents", [])

        if status == "healthy" and not active:
            log("[VERIFY] ✅ Service fully recovered!")
            return True

        log(f"[VERIFY] Still {status} — active: {active}")

        # After 3 failed attempts, try direct fallback remediation
        if attempt == 3 and incident_types:
            log("[VERIFY] ⚠️ n8n did not resolve — trying direct fallback...")
            for inc_type in incident_types:
                direct_remediate(inc_type)

    log("[VERIFY] ❌ Service did NOT recover within timeout")
    return False


def main_loop():
    """Main autonomous detection → remediation → verification loop."""
    log("=" * 60)
    log("  Autonomous Cloud Incident System — STARTED")
    log(f"  Poll interval: {POLL_INTERVAL}s | Verify delay: {VERIFY_DELAY}s")
    log("=" * 60)

    # Quick health check at startup
    health = check_health()
    log(f"Initial health: {health.get('status', 'unknown')}")

    while True:
        try:
            # ── PHASE 1: Detection ──
            incidents = detect_incidents()

            if not incidents:
                log("✅ No incidents — system healthy")
                time.sleep(POLL_INTERVAL)
                continue

            # ── PHASE 2: Trigger remediation via n8n ──
            for incident in incidents:
                inc_type = incident["type"]
                details = incident["details"]

                log(f"🚨 INCIDENT DETECTED: {inc_type}")
                log(f"   Details: {details}")

                # Send to n8n production webhook
                result = trigger_remediation(inc_type, details)
                log(f"   n8n response: {result.get('status', 'unknown')}")

            # ── PHASE 3: Verification ──
            log(f"⏳ Waiting {VERIFY_DELAY}s before verification...")
            inc_types = [i["type"] for i in incidents]
            recovered = run_verification_loop(inc_types)

            if recovered:
                log("🎉 REMEDIATION CYCLE COMPLETE — service restored")
            else:
                log("⚠️ REMEDIATION CYCLE INCOMPLETE — manual review needed")

            # ── Cooldown before next scan ──
            log(f"⏳ Cooldown {COOLDOWN}s before next scan...")
            time.sleep(COOLDOWN)

        except KeyboardInterrupt:
            log("🛑 Shutting down (Ctrl+C)")
            break
        except Exception as e:
            log(f"❌ Unexpected error in main loop: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main_loop()
>>>>>>> Stashed changes
