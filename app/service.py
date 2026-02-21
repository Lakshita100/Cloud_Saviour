"""
Autonomous Cloud Incident System — Monitored Microservice
Exposes CPU, memory, error count, and latency metrics via Prometheus.
Includes incident-injection endpoints for live simulation.
"""

import asyncio
import time
import random
import psutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# ──────────────────────────────────────────────
# Prometheus Metrics
# ──────────────────────────────────────────────
CPU_USAGE = Gauge(
    "service_cpu_usage_percent",
    "Current CPU usage percentage",
)
MEMORY_USAGE = Gauge(
    "service_memory_usage_percent",
    "Current memory usage percentage",
)
ERROR_COUNTER = Counter(
    "service_errors_total",
    "Total number of errors",
    ["error_type"],
)
REQUEST_LATENCY = Histogram(
    "service_request_latency_seconds",
    "Request latency in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ──────────────────────────────────────────────
# Service state (used by /health and remediation)
# ──────────────────────────────────────────────
_service_state = {
    "crashed": False,
    "degraded": False,
    "memory_leak_active": False,
    "db_overload_active": False,
    "latency_spike_active": False,
    "cpu_spike_active": False,
}

# ──────────────────────────────────────────────
# Background task: refresh system metrics every 5 s
# ──────────────────────────────────────────────
async def _refresh_system_metrics():
    while True:
        CPU_USAGE.set(psutil.cpu_percent(interval=None))
        MEMORY_USAGE.set(psutil.virtual_memory().percent)
        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_refresh_system_metrics())
    yield
    task.cancel()


# ──────────────────────────────────────────────
# FastAPI Application
# ──────────────────────────────────────────────
app = FastAPI(
    title="Cloud Incident Service",
    version="1.0.0",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# Middleware — track latency for every request
# ──────────────────────────────────────────────
@app.middleware("http")
async def track_latency(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    REQUEST_LATENCY.observe(elapsed)
    return response


# ──────────────────────────────────────────────
# Core Endpoints
# ──────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "running", "service": "cloud-incident-service"}


@app.get("/health")
async def health():
    if _service_state["crashed"]:
        status = "crashed"
    elif _service_state["degraded"] or any(
        _service_state[k] for k in (
            "memory_leak_active", "db_overload_active",
            "latency_spike_active", "cpu_spike_active",
        )
    ):
        status = "degraded"
    else:
        status = "healthy"
    return {
        "status": status,
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent": psutil.virtual_memory().percent,
        "active_incidents": [
            k for k, v in _service_state.items() if v and k not in ("degraded",)
        ],
    }


@app.get("/metrics")
async def metrics():
    """Prometheus scrape endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ──────────────────────────────────────────────
# Incident Injection Endpoints
# ──────────────────────────────────────────────
_leak_store: list[bytes] = []  # holds leaked memory blocks


@app.post("/trigger/memory_leak")
async def trigger_memory_leak():
    """Allocate ~50 MB per call to simulate a memory leak."""
    chunk = bytearray(50 * 1024 * 1024)  # 50 MB
    _leak_store.append(bytes(chunk))
    _service_state["memory_leak_active"] = True
    ERROR_COUNTER.labels(error_type="memory_leak").inc()
    return {
        "incident": "memory_leak",
        "allocated_mb": len(_leak_store) * 50,
        "message": f"Leaked {len(_leak_store) * 50} MB total",
    }


@app.post("/trigger/db_overload")
async def trigger_db_overload():
    """Simulate a slow / overloaded database call."""
    _service_state["db_overload_active"] = True
    delay = random.uniform(2.0, 5.0)
    await asyncio.sleep(delay)
    ERROR_COUNTER.labels(error_type="db_overload").inc()
    return {
        "incident": "db_overload",
        "simulated_delay_s": round(delay, 2),
        "message": "Simulated database overload with high latency",
    }


@app.post("/trigger/crash")
async def trigger_crash():
    """Mark service as crashed and raise an unhandled exception."""
    _service_state["crashed"] = True
    ERROR_COUNTER.labels(error_type="crash").inc()
    raise RuntimeError("Simulated service crash triggered via /trigger/crash")


@app.post("/trigger/cpu_spike")
async def trigger_cpu_spike():
    """Burn CPU for ~4 seconds to simulate a CPU spike."""
    import math
    _service_state["cpu_spike_active"] = True
    ERROR_COUNTER.labels(error_type="cpu_spike").inc()
    end = time.time() + 4
    while time.time() < end:
        math.factorial(5000)
    _service_state["cpu_spike_active"] = False
    return {
        "incident": "cpu_spike",
        "duration_s": 4,
        "message": "Simulated CPU spike for 4 seconds",
    }


@app.post("/trigger/latency_spike")
async def trigger_latency_spike():
    """Inject a random 3–8 s delay to simulate network / upstream latency."""
    _service_state["latency_spike_active"] = True
    delay = random.uniform(3.0, 8.0)
    await asyncio.sleep(delay)
    ERROR_COUNTER.labels(error_type="latency_spike").inc()
    _service_state["latency_spike_active"] = False
    return {
        "incident": "latency_spike",
        "simulated_delay_s": round(delay, 2),
        "message": "Simulated latency spike",
    }


# ──────────────────────────────────────────────
# Remediation Endpoints (called by n8n / agent)
# ──────────────────────────────────────────────
@app.post("/remediate/memory_leak")
async def remediate_memory_leak():
    """Free all leaked memory and reset state."""
    freed_mb = len(_leak_store) * 50
    _leak_store.clear()
    _service_state["memory_leak_active"] = False
    return {
        "remediation": "memory_leak",
        "freed_mb": freed_mb,
        "message": f"Cleared {freed_mb} MB of leaked memory",
    }


@app.post("/remediate/db_overload")
async def remediate_db_overload():
    """Reset the database overload state."""
    _service_state["db_overload_active"] = False
    return {
        "remediation": "db_overload",
        "message": "Database overload state cleared",
    }


@app.post("/remediate/crash")
async def remediate_crash():
    """Reset crash flag so /health returns healthy again."""
    _service_state["crashed"] = False
    return {
        "remediation": "crash",
        "message": "Crash state cleared, service marked healthy",
    }


@app.post("/restart")
async def restart_service():
    """Full reset — clear all incident state and leaked memory."""
    _leak_store.clear()
    for key in _service_state:
        _service_state[key] = False
    return {
        "remediation": "full_restart",
        "message": "All incident states cleared, service fully restored",
        "state": dict(_service_state),
    }


# ──────────────────────────────────────────────
# Verification State Endpoint
# ──────────────────────────────────────────────
@app.get("/state")
async def get_state():
    """Return the full internal service state for verification."""
    return {
        "service_state": dict(_service_state),
        "leaked_memory_mb": len(_leak_store) * 50,
        "cpu_percent": psutil.cpu_percent(interval=None),
        "memory_percent": psutil.virtual_memory().percent,
    }


# ──────────────────────────────────────────────
# Run with: uvicorn app.service:app --host 0.0.0.0 --port 8000
# ──────────────────────────────────────────────
