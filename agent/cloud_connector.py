"""
Cloud Connector — Fetches metrics from Prometheus or directly from the service.

Tries Prometheus first (port 9090). Falls back to the service /metrics endpoint.
"""

import re
import requests

PROM_URL = "http://localhost:9090/api/v1/query"
SERVICE_METRICS_URL = "http://127.0.0.1:8000/metrics"


def query_prometheus(query: str) -> dict:
    """Query the Prometheus HTTP API."""
    response = requests.get(PROM_URL, params={"query": query}, timeout=5)
    return response.json()


def _parse_service_metrics() -> dict:
    """Fetch /metrics from the service and parse Prometheus text format."""
    resp = requests.get(SERVICE_METRICS_URL, timeout=5)
    parsed = {}
    for line in resp.text.splitlines():
        if line.startswith("#"):
            continue
        match = re.match(r'^(\S+)\s+([\d.eE+-]+)$', line)
        if match:
            parsed[match.group(1)] = float(match.group(2))
    return parsed


def fetch_metrics() -> dict:
    """
    Return key metrics as a dict.

    Tries Prometheus API first; falls back to scraping /metrics directly.
    """
    # Try Prometheus
    try:
        error_query = 'service_errors_total{error_type="memory_leak"}'
        result = query_prometheus(error_query)
        error_count = float(result["data"]["result"][0]["value"][1])
    except Exception:
        # Fallback: parse /metrics from the service directly
        try:
            parsed = _parse_service_metrics()
            error_count = parsed.get('service_errors_total{error_type="memory_leak"}', 0.0)
        except Exception:
            error_count = 0.0

    # Also grab CPU and memory if available
    try:
        parsed = parsed if "parsed" in dir() else _parse_service_metrics()
        cpu = parsed.get("service_cpu_usage_percent", 0.0)
        mem = parsed.get("service_memory_usage_percent", 0.0)
    except Exception:
        cpu = 0.0
        mem = 0.0

    return {
        "error_count": error_count,
        "cpu_percent": cpu,
        "memory_percent": mem,
    }