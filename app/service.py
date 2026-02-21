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
from fastapi.middleware.cors import CORSMiddleware
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
# CORS — allow React frontend
# ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    global _last_incident
    chunk = bytearray(50 * 1024 * 1024)  # 50 MB
    _leak_store.append(bytes(chunk))
    _service_state["memory_leak_active"] = True
    ERROR_COUNTER.labels(error_type="memory_leak").inc()
    _add_event(f"MEMORY LEAK injected — {len(_leak_store) * 50} MB leaked")
    _last_incident = {"id": f"INC-ML-{int(time.time())}", "type": "MEMORY_LEAK", "severity": "HIGH", "status": "Detected"}
    return {
        "incident": "memory_leak",
        "allocated_mb": len(_leak_store) * 50,
        "message": f"Leaked {len(_leak_store) * 50} MB total",
    }


@app.post("/trigger/db_overload")
async def trigger_db_overload():
    """Simulate a slow / overloaded database call."""
    global _last_incident
    _service_state["db_overload_active"] = True
    _add_event("DB OVERLOAD injected")
    _last_incident = {"id": f"INC-DB-{int(time.time())}", "type": "DB_OVERLOAD", "severity": "HIGH", "status": "Detected"}
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
    global _last_incident
    _service_state["crashed"] = True
    ERROR_COUNTER.labels(error_type="crash").inc()
    _add_event("CRASH injected — service marked crashed")
    _last_incident = {"id": f"INC-CR-{int(time.time())}", "type": "CRASH", "severity": "HIGH", "status": "Detected"}
    raise RuntimeError("Simulated service crash triggered via /trigger/crash")


@app.post("/trigger/cpu_spike")
async def trigger_cpu_spike():
    """Burn CPU for ~4 seconds to simulate a CPU spike."""
    global _last_incident
    import math
    _service_state["cpu_spike_active"] = True
    ERROR_COUNTER.labels(error_type="cpu_spike").inc()
    _add_event("CPU SPIKE injected — burning CPU for 4s")
    _last_incident = {"id": f"INC-CS-{int(time.time())}", "type": "CPU_SPIKE", "severity": "MEDIUM", "status": "Detected"}
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
    global _last_incident
    _service_state["latency_spike_active"] = True
    _add_event("LATENCY SPIKE injected")
    _last_incident = {"id": f"INC-LS-{int(time.time())}", "type": "LATENCY_SPIKE", "severity": "MEDIUM", "status": "Detected"}
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
    _add_event(f"Memory leak remediated — freed {freed_mb} MB")
    return {
        "remediation": "memory_leak",
        "freed_mb": freed_mb,
        "message": f"Cleared {freed_mb} MB of leaked memory",
    }


@app.post("/remediate/db_overload")
async def remediate_db_overload():
    """Reset the database overload state."""
    _service_state["db_overload_active"] = False
    _add_event("DB overload remediated")
    return {
        "remediation": "db_overload",
        "message": "Database overload state cleared",
    }


@app.post("/remediate/crash")
async def remediate_crash():
    """Reset crash flag so /health returns healthy again."""
    _service_state["crashed"] = False
    _add_event("Crash state cleared — service recovered")
    return {
        "remediation": "crash",
        "message": "Crash state cleared, service marked healthy",
    }


@app.post("/restart")
async def restart_service():
    """Full reset — clear all incident state and leaked memory."""
    global _last_incident, _last_rca, _last_remediation, _last_risk
    _leak_store.clear()
    for key in _service_state:
        _service_state[key] = False
    _last_incident = None
    _last_rca = None
    _last_remediation = None
    _last_risk = None
    _add_event("Full restart — all states cleared")
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
# Dashboard API Endpoints (consumed by React frontend)
# ──────────────────────────────────────────────
import sys, os, re as _re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Shared state for timeline events and last pipeline results
_timeline_events: list[dict] = []
_last_incident: dict | None = None
_last_rca: dict | None = None
_last_remediation: dict | None = None
_last_risk: dict | None = None


def _add_event(message: str):
    """Add a timestamped event to the timeline."""
    from datetime import datetime
    ts = datetime.now().strftime("%H:%M:%S")
    _timeline_events.insert(0, {"timestamp": ts, "message": message})
    if len(_timeline_events) > 50:
        _timeline_events.pop()


@app.get("/api/dashboard")
async def api_dashboard():
    """
    Single endpoint that returns all data the React frontend needs.
    Matches the DashboardData interface exactly.
    """
    # Get current metrics
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent

    # Parse error count from Prometheus metrics
    prom_text = generate_latest().decode("utf-8")
    error_count = 0.0
    for line in prom_text.splitlines():
        if line.startswith("service_errors_total"):
            match = _re.search(r'\}\s+([\d.]+)', line)
            if match:
                error_count += float(match.group(1))

    # Parse latency p95 (approximate from histogram)
    latency_p95 = 0.0
    for line in prom_text.splitlines():
        if 'service_request_latency_seconds_bucket{le="1.0"}' in line:
            match = _re.search(r'\s+([\d.]+)$', line)
            if match:
                latency_p95 = float(match.group(1))

    # Health status
    if _service_state["crashed"]:
        status = "crashed"
    elif any(_service_state[k] for k in (
        "memory_leak_active", "db_overload_active",
        "latency_spike_active", "cpu_spike_active",
    )):
        status = "degraded"
    else:
        status = "healthy"

    active = [k for k, v in _service_state.items() if v and k not in ("degraded",)]

    # Build incident for frontend (Incident interface)
    incident = None
    if _last_incident:
        incident = _last_incident
    elif status != "healthy":
        from datetime import datetime
        inc_type = active[0].replace("_active", "").upper() if active else "UNKNOWN"
        incident = {
            "id": f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "type": inc_type.replace("_", " ").title(),
            "severity": "HIGH" if status == "crashed" else "MEDIUM",
            "status": "Detected",
        }

    return {
        "metrics": {
            "cpu": round(cpu, 1),
            "memory": round(mem, 1),
            "dbConnections": 24 if not _service_state["db_overload_active"] else 89,
            "errorRate": round(error_count, 2),
            "latencyP95": round(latency_p95 * 1000, 0),  # convert to ms
            "deploymentVersion": "v1.0.0",
        },
        "incident": incident,
        "rca": _last_rca,
        "remediation": _last_remediation,
        "timeline": _timeline_events[:20],
        "health": {
            "status": status,
            "active_incidents": active,
        },
    }


@app.post("/api/pipeline")
async def api_run_pipeline():
    """
    Run the full AI pipeline: Detect → RCA → Risk → Remediate → Verify.

    IMPORTANT: All detection and remediation reads/writes use in-process
    state directly.  We must NOT make HTTP calls back to ourselves because
    the async event-loop would deadlock (the blocking `requests.get` call
    prevents the server from handling its own /health response).
    """
    global _last_incident, _last_rca, _last_remediation, _last_risk
    import asyncio
    from datetime import datetime

    _add_event("Pipeline triggered from dashboard")

    # Import agent modules (external calls only — Ollama is on a *different* port)
    from agent.context_builder import build_context
    from agent.rca_engine import run_rca
    from agent.risk_engine import calculate_risk_score
    from agent.anomaly_engine import detect_anomalies
    from agent.knowledge_base import get_common_causes

    # ── Phase 1: Detection (direct state read — no HTTP) ──
    _add_event("Running incident detection...")
    incidents: list[dict] = []
    state = _service_state  # read in-process dict

    if state["crashed"]:
        incidents.append({"type": "CRASH", "details": {"reason": "Service reports crashed"}})
    if state["memory_leak_active"]:
        incidents.append({"type": "MEMORY_LEAK", "details": {"memory_percent": psutil.virtual_memory().percent}})
    if state["db_overload_active"]:
        incidents.append({"type": "DB_OVERLOAD", "details": {"flagged_by": "state"}})
    if state["cpu_spike_active"]:
        incidents.append({"type": "CPU_SPIKE", "details": {"cpu_percent": psutil.cpu_percent(interval=None)}})
    if state["latency_spike_active"]:
        incidents.append({"type": "LATENCY_SPIKE", "details": {"flagged_by": "state"}})

    # Threshold-based detection
    cpu_now = psutil.cpu_percent(interval=None)
    mem_now = psutil.virtual_memory().percent
    if mem_now > 90 and not any(i["type"] == "MEMORY_LEAK" for i in incidents):
        incidents.append({"type": "MEMORY_LEAK", "details": {"memory_percent": mem_now, "flagged_by": "threshold"}})
    if cpu_now > 85 and not any(i["type"] == "CPU_SPIKE" for i in incidents):
        incidents.append({"type": "CPU_SPIKE", "details": {"cpu_percent": cpu_now, "flagged_by": "threshold"}})

    # Build a metrics dict for downstream modules (no HTTP call)
    metrics = {
        "cpu_percent": cpu_now,
        "memory_percent": mem_now,
        "error_count": sum(
            sample.value
            for metric in ERROR_COUNTER.collect()
            for sample in metric.samples
            if sample.name.endswith("_total")
        ),
    }

    if not incidents:
        _add_event("No incidents detected — system healthy")
        _last_incident = None
        _last_rca = None
        _last_remediation = None
        return {"status": "healthy", "message": "No incidents detected"}

    # Process first (most critical) incident
    inc = incidents[0]
    inc_type = inc["type"]
    details = inc.get("details", {})

    _last_incident = {
        "id": f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "type": inc_type.replace("_", " ").title(),
        "severity": "HIGH",
        "status": "Detected",
    }
    _add_event(f"Incident detected: {inc_type}")

    # ── Phase 2: AI RCA (Ollama is external on :11434 — safe) ──
    _add_event("Running AI Root Cause Analysis...")
    rca_raw: dict = {}
    try:
        prompt = build_context(metrics, inc)
        rca_raw = await asyncio.to_thread(run_rca, prompt)  # blocking → thread
        model_used = rca_raw.get("_model_used", "ollama")
        confidence_raw = rca_raw.get("confidence", 0)
        # Normalise: if model returned 0-1, multiply by 100; if already %, keep
        confidence_pct = round(confidence_raw * 100) if confidence_raw <= 1 else round(confidence_raw)
        _last_rca = {
            "rootCause": rca_raw.get("root_cause", "Unknown"),
            "confidence": max(confidence_pct, 1),  # never show 0% if AI responded
            "impactScope": rca_raw.get("reasoning", "N/A")[:200],
            "remediationSteps": [
                rca_raw.get("recommended_action", "Manual investigation required")
            ] + get_common_causes(inc_type)[:3],
        }
        _last_incident["status"] = "RCA Complete"
        _add_event(f"RCA complete ({model_used}): {rca_raw.get('root_cause', 'Unknown')} "
                   f"(confidence: {rca_raw.get('confidence', 0):.0%})")
    except Exception as e:
        _last_rca = {
            "rootCause": f"AI unavailable: {str(e)[:100]}",
            "confidence": 0,
            "impactScope": "AI engine could not be reached",
            "remediationSteps": get_common_causes(inc_type)[:4],
        }
        _add_event(f"AI RCA failed: {e}")

    # ── Phase 3: Risk scoring ──
    anomalies = detect_anomalies(metrics)
    risk = calculate_risk_score(inc_type, metrics, rca_raw or None, anomalies)
    _last_risk = risk
    _add_event(f"Risk score: {risk['risk_score']} ({risk['risk_level']})")

    # ── Phase 4: Remediation (direct state mutation — no HTTP) ──
    _add_event(f"Orchestrating remediation for {inc_type}...")
    rem_start = time.time()
    remediated = False

    # Try n8n webhook first (external, safe)
    try:
        import requests as _req
        n8n_resp = await asyncio.to_thread(
            lambda: _req.post(
                "http://localhost:5678/webhook/remediation",
                json={"incident_type": inc_type, "details": details, "risk": risk["risk_score"]},
                timeout=10,
            )
        )
        if n8n_resp.status_code == 200:
            remediated = True
            _add_event("n8n workflow executed remediation")
    except Exception:
        _add_event("n8n unreachable — using direct remediation fallback")

    # Direct state remediation (in-process, always works)
    if inc_type == "MEMORY_LEAK":
        freed = len(_leak_store) * 50
        _leak_store.clear()
        state["memory_leak_active"] = False
        _add_event(f"Memory leak remediated — freed {freed} MB")
        remediated = True
    elif inc_type == "DB_OVERLOAD":
        state["db_overload_active"] = False
        _add_event("DB overload state cleared")
        remediated = True
    elif inc_type == "CRASH":
        state["crashed"] = False
        _add_event("Crash state cleared — service recovered")
        remediated = True
    elif inc_type == "CPU_SPIKE":
        state["cpu_spike_active"] = False
        _add_event("CPU spike state cleared")
        remediated = True
    elif inc_type == "LATENCY_SPIKE":
        state["latency_spike_active"] = False
        _add_event("Latency spike state cleared")
        remediated = True

    elapsed = round(time.time() - rem_start, 1)
    _last_remediation = {
        "riskAssessment": "High Risk" if risk["risk_level"] in ("high", "critical") else "Low Risk",
        "actionTaken": f"Remediation for {inc_type.replace('_', ' ').lower()}",
        "executionTime": elapsed,
        "recoveryStatus": "Success" if remediated else "Failed",
    }
    _last_incident["status"] = "Remediated" if remediated else "RCA Complete"
    _add_event(f"Remediation {'succeeded' if remediated else 'failed'} ({elapsed}s)")

    # ── Phase 5: Verification (direct state check) ──
    active_after = [k for k, v in state.items() if v and k not in ("degraded",)]
    if not active_after:
        _add_event("System recovered — all metrics nominal")
    else:
        _add_event(f"System still degraded: {active_after}")

    return {
        "status": "complete",
        "incident": _last_incident,
        "rca": _last_rca,
        "remediation": _last_remediation,
        "risk": _last_risk,
    }


async def api_health_check() -> dict:
    """Internal helper to check health."""
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    if _service_state["crashed"]:
        status = "crashed"
    elif any(_service_state[k] for k in (
        "memory_leak_active", "db_overload_active",
        "latency_spike_active", "cpu_spike_active",
    )):
        status = "degraded"
    else:
        status = "healthy"
    return {
        "status": status,
        "active_incidents": [k for k, v in _service_state.items() if v and k != "degraded"],
    }


# ──────────────────────────────────────────────
# Run with: uvicorn app.service:app --host 0.0.0.0 --port 8000
# ──────────────────────────────────────────────
