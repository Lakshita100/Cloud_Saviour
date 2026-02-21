previous_value = None
incident_active = False

def detect_incident(metrics):
    global previous_value, incident_active

    current = metrics.get("error_count", 0)

    # First run
    if previous_value is None:
        previous_value = current
        return None

    trend = current - previous_value
    previous_value = current

    # Detect only if rising and not already active
    if current > 5 and trend > 1 and not incident_active:
        incident_active = True
        return {
            "type": "MEMORY_LEAK",
            "severity": "HIGH",
            "current_value": current,
            "trend": trend
        }

    return None
"""
Detector — Polls the microservice and detects anomalies.

Checks /health and /metrics to identify:
  - MEMORY_LEAK   (memory > threshold)
  - DB_OVERLOAD   (high latency + db_overload flag)
  - CRASH         (service crashed or unreachable)
  - CPU_SPIKE     (CPU > threshold)
  - LATENCY_SPIKE (latency > threshold)

Also exposes detect_incident(metrics) for simple error-count based detection.
"""

import requests
import re

SERVICE_URL = "http://127.0.0.1:8000"

# ── Thresholds ──
MEMORY_THRESHOLD = 85.0    # percent
CPU_THRESHOLD = 80.0       # percent
LATENCY_THRESHOLD = 2.0    # seconds (p99)

# ── Simple trend-based state (used by detect_incident) ──
_previous_value = None
_incident_active = False


def check_health() -> dict:
    """Poll /health and return parsed result."""
    try:
        resp = requests.get(f"{SERVICE_URL}/health", timeout=5)
        return resp.json()
    except requests.ConnectionError:
        return {"status": "unreachable", "active_incidents": []}
    except Exception as e:
        return {"status": "error", "error": str(e), "active_incidents": []}


def check_metrics() -> dict:
    """Poll /metrics and parse Prometheus text into a dict."""
    try:
        resp = requests.get(f"{SERVICE_URL}/metrics", timeout=5)
        text = resp.text
        result = {}

        # Parse gauge / counter values
        for line in text.splitlines():
            if line.startswith("#"):
                continue
            # e.g. service_cpu_usage_percent 45.2
            match = re.match(r'^(\S+)\s+([\d.eE+-]+)$', line)
            if match:
                result[match.group(1)] = float(match.group(2))

        return result
    except Exception:
        return {}


def detect_incidents() -> list[dict]:
    """
    Run all detection checks and return a list of detected incidents.

    Each incident is a dict: {"type": "MEMORY_LEAK", "details": {...}}
    """
    incidents = []

    # 1. Check /health first
    health = check_health()
    status = health.get("status", "unknown")
    active = health.get("active_incidents", [])

    if status == "unreachable":
        incidents.append({
            "type": "CRASH",
            "details": {"reason": "Service unreachable", "status": status},
        })
        return incidents  # Can't check metrics if service is down

    if status == "crashed":
        incidents.append({
            "type": "CRASH",
            "details": {"reason": "Service reports crashed", "active": active},
        })

    # 2. Check for flagged incidents from /health
    if "memory_leak_active" in active:
        incidents.append({
            "type": "MEMORY_LEAK",
            "details": {
                "memory_percent": health.get("memory_percent", 0),
                "flagged_by": "health_endpoint",
            },
        })

    if "db_overload_active" in active:
        incidents.append({
            "type": "DB_OVERLOAD",
            "details": {"flagged_by": "health_endpoint"},
        })

    if "cpu_spike_active" in active:
        incidents.append({
            "type": "CPU_SPIKE",
            "details": {
                "cpu_percent": health.get("cpu_percent", 0),
                "flagged_by": "health_endpoint",
            },
        })

    if "latency_spike_active" in active:
        incidents.append({
            "type": "LATENCY_SPIKE",
            "details": {"flagged_by": "health_endpoint"},
        })

    # 3. Threshold-based detection from metrics
    metrics = check_metrics()

    cpu = metrics.get("service_cpu_usage_percent", 0)
    mem = metrics.get("service_memory_usage_percent", 0)

    if mem > MEMORY_THRESHOLD and not any(i["type"] == "MEMORY_LEAK" for i in incidents):
        incidents.append({
            "type": "MEMORY_LEAK",
            "details": {
                "memory_percent": mem,
                "threshold": MEMORY_THRESHOLD,
                "flagged_by": "metric_threshold",
            },
        })

    if cpu > CPU_THRESHOLD and not any(i["type"] == "CPU_SPIKE" for i in incidents):
        incidents.append({
            "type": "CPU_SPIKE",
            "details": {
                "cpu_percent": cpu,
                "threshold": CPU_THRESHOLD,
                "flagged_by": "metric_threshold",
            },
        })

    return incidents


def detect_incident(metrics: dict) -> dict | None:
    """
    Simple error-count trend-based detection (used by cloud_connector flow).

    Returns an incident dict if error_count is rising, else None.
    """
    global _previous_value, _incident_active

    current = metrics.get("error_count", 0)

    # First run — baseline
    if _previous_value is None:
        _previous_value = current
        return None

    trend = current - _previous_value
    _previous_value = current

    # Detect only if rising and not already active
    if current > 5 and trend > 1 and not _incident_active:
        _incident_active = True
        return {
            "type": "MEMORY_LEAK",
            "severity": "HIGH",
            "current_value": current,
            "trend": trend,
        }

    # Reset active flag once error count drops
    if current <= 1:
        _incident_active = False

    return None


# ── Direct test ──
if __name__ == "__main__":
    print("=== Running detection scan ===\n")

    health = check_health()
    print(f"Health: {health}\n")

    metrics = check_metrics()
    print(f"Key metrics:")
    for k, v in metrics.items():
        if "service_" in k and "bucket" not in k and "created" not in k:
            print(f"  {k} = {v}")

    print()
    incidents = detect_incidents()
    if incidents:
        for inc in incidents:
            print(f"  🚨 {inc['type']}: {inc['details']}")
    else:
        print("  ✅ No incidents detected")
