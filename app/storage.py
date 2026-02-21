"""
Persistent Storage Layer — SQLite-backed incident, metrics, and audit storage.

Replaces in-memory-only state with durable storage that survives restarts.
Provides:
  - Incident history (all past incidents with full lifecycle)
  - Metrics snapshots (time-series for dashboard charts)
  - Audit log (who did what, when, from where)
  - Learning records (resolved incidents used to improve KB)
"""

import sqlite3
import json
import os
import threading
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cloudsaviour.db")
_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """Return a thread-local SQLite connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db():
    """Create all tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS incidents (
            id          TEXT PRIMARY KEY,
            type        TEXT NOT NULL,
            severity    TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'detected',
            details     TEXT DEFAULT '{}',
            metrics_snapshot TEXT DEFAULT '{}',
            rca_result  TEXT DEFAULT NULL,
            risk_score  REAL DEFAULT NULL,
            risk_level  TEXT DEFAULT NULL,
            remediation_result TEXT DEFAULT NULL,
            resolved_at TEXT DEFAULT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS metrics_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu         REAL NOT NULL,
            memory      REAL NOT NULL,
            error_count REAL DEFAULT 0,
            latency_p95 REAL DEFAULT 0,
            db_connections INTEGER DEFAULT 0,
            recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            action      TEXT NOT NULL,
            endpoint    TEXT NOT NULL,
            method      TEXT NOT NULL DEFAULT 'GET',
            api_key_name TEXT DEFAULT 'anonymous',
            source_ip   TEXT DEFAULT 'unknown',
            details     TEXT DEFAULT '{}',
            timestamp   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS learning_records (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_type   TEXT NOT NULL,
            root_cause      TEXT NOT NULL,
            confidence      REAL NOT NULL,
            was_correct     INTEGER DEFAULT 1,
            remediation_action TEXT DEFAULT '',
            remediation_success INTEGER DEFAULT 1,
            model_used      TEXT DEFAULT '',
            metrics_context TEXT DEFAULT '{}',
            feedback        TEXT DEFAULT '',
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(type);
        CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
        CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at);
        CREATE INDEX IF NOT EXISTS idx_metrics_recorded ON metrics_history(recorded_at);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_records(incident_type);
    """)
    conn.commit()


# ──────────────────────────────────────────────
# Incident CRUD
# ──────────────────────────────────────────────

def save_incident(incident: dict) -> str:
    """Insert or update an incident record."""
    conn = _get_conn()
    inc_id = incident.get("id", f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    conn.execute("""
        INSERT INTO incidents (id, type, severity, status, details, metrics_snapshot, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        ON CONFLICT(id) DO UPDATE SET
            status = excluded.status,
            updated_at = datetime('now')
    """, (
        inc_id,
        incident.get("type", "UNKNOWN"),
        incident.get("severity", "MEDIUM"),
        incident.get("status", "detected"),
        json.dumps(incident.get("details", {})),
        json.dumps(incident.get("metrics_snapshot", {})),
    ))
    conn.commit()
    return inc_id


def update_incident(inc_id: str, **kwargs):
    """Update specific fields on an incident."""
    conn = _get_conn()
    allowed = {
        "status", "rca_result", "risk_score", "risk_level",
        "remediation_result", "resolved_at",
    }
    sets = []
    vals = []
    for k, v in kwargs.items():
        if k in allowed:
            if isinstance(v, (dict, list)):
                v = json.dumps(v)
            sets.append(f"{k} = ?")
            vals.append(v)
    if sets:
        sets.append("updated_at = datetime('now')")
        vals.append(inc_id)
        conn.execute(f"UPDATE incidents SET {', '.join(sets)} WHERE id = ?", vals)
        conn.commit()


def get_incident(inc_id: str) -> dict | None:
    """Fetch a single incident by ID."""
    conn = _get_conn()
    row = conn.execute("SELECT * FROM incidents WHERE id = ?", (inc_id,)).fetchone()
    return _row_to_dict(row) if row else None


def get_recent_incidents(limit: int = 50) -> list[dict]:
    """Fetch the most recent incidents."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_incidents_by_type(incident_type: str, limit: int = 20) -> list[dict]:
    """Fetch recent incidents of a specific type."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM incidents WHERE type = ? ORDER BY created_at DESC LIMIT ?",
        (incident_type, limit)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_incident_stats() -> dict:
    """Get aggregated incident statistics."""
    conn = _get_conn()
    total = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM incidents WHERE status = 'remediated'").fetchone()[0]
    by_type = {}
    for row in conn.execute("SELECT type, COUNT(*) as cnt FROM incidents GROUP BY type").fetchall():
        by_type[row["type"]] = row["cnt"]
    by_severity = {}
    for row in conn.execute("SELECT severity, COUNT(*) as cnt FROM incidents GROUP BY severity").fetchall():
        by_severity[row["severity"]] = row["cnt"]
    return {
        "total": total,
        "resolved": resolved,
        "resolution_rate": round(resolved / max(total, 1) * 100, 1),
        "by_type": by_type,
        "by_severity": by_severity,
    }


# ──────────────────────────────────────────────
# Metrics History
# ──────────────────────────────────────────────

def save_metrics_snapshot(cpu: float, memory: float, error_count: float = 0,
                          latency_p95: float = 0, db_connections: int = 0):
    """Record a point-in-time metrics snapshot."""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO metrics_history (cpu, memory, error_count, latency_p95, db_connections)
        VALUES (?, ?, ?, ?, ?)
    """, (cpu, memory, error_count, latency_p95, db_connections))
    conn.commit()


def get_metrics_history(minutes: int = 60, limit: int = 200) -> list[dict]:
    """Fetch recent metrics history."""
    conn = _get_conn()
    rows = conn.execute("""
        SELECT * FROM metrics_history
        WHERE recorded_at >= datetime('now', ?)
        ORDER BY recorded_at DESC LIMIT ?
    """, (f"-{minutes} minutes", limit)).fetchall()
    return [dict(r) for r in rows]


def cleanup_old_metrics(days: int = 7):
    """Delete metrics older than N days to prevent unbounded growth."""
    conn = _get_conn()
    conn.execute(
        "DELETE FROM metrics_history WHERE recorded_at < datetime('now', ?)",
        (f"-{days} days",)
    )
    conn.commit()


# ──────────────────────────────────────────────
# Audit Log
# ──────────────────────────────────────────────

def log_audit(action: str, endpoint: str, method: str = "GET",
              api_key_name: str = "anonymous", source_ip: str = "unknown",
              details: dict | None = None):
    """Record an audit log entry."""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO audit_log (action, endpoint, method, api_key_name, source_ip, details)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (action, endpoint, method, api_key_name, source_ip, json.dumps(details or {})))
    conn.commit()


def get_audit_log(limit: int = 100) -> list[dict]:
    """Fetch recent audit log entries."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_audit_log_for_key(api_key_name: str, limit: int = 50) -> list[dict]:
    """Fetch audit entries for a specific API key."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM audit_log WHERE api_key_name = ? ORDER BY timestamp DESC LIMIT ?",
        (api_key_name, limit)
    ).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────
# Learning Records
# ──────────────────────────────────────────────

def save_learning_record(incident_type: str, root_cause: str, confidence: float,
                         remediation_action: str = "", remediation_success: bool = True,
                         model_used: str = "", metrics_context: dict | None = None):
    """Save a resolved incident as a learning record for future reference."""
    conn = _get_conn()
    conn.execute("""
        INSERT INTO learning_records
        (incident_type, root_cause, confidence, remediation_action,
         remediation_success, model_used, metrics_context)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        incident_type, root_cause, confidence, remediation_action,
        1 if remediation_success else 0, model_used,
        json.dumps(metrics_context or {}),
    ))
    conn.commit()


def get_learning_records(incident_type: str | None = None, limit: int = 50) -> list[dict]:
    """Fetch learning records, optionally filtered by incident type."""
    conn = _get_conn()
    if incident_type:
        rows = conn.execute(
            "SELECT * FROM learning_records WHERE incident_type = ? ORDER BY created_at DESC LIMIT ?",
            (incident_type, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM learning_records ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_learning_summary(incident_type: str) -> dict:
    """
    Build a learning summary for an incident type.
    Returns most common root causes, success rates, and best remediation actions.
    """
    records = get_learning_records(incident_type, limit=100)
    if not records:
        return {"total_records": 0, "top_root_causes": [], "success_rate": 0, "avg_confidence": 0}

    # Count root causes
    cause_counts: dict[str, int] = {}
    success_count = 0
    total_conf = 0.0

    for r in records:
        cause = r.get("root_cause", "Unknown")
        cause_counts[cause] = cause_counts.get(cause, 0) + 1
        if r.get("remediation_success"):
            success_count += 1
        total_conf += r.get("confidence", 0)

    top_causes = sorted(cause_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_records": len(records),
        "top_root_causes": [{"cause": c, "count": n} for c, n in top_causes],
        "success_rate": round(success_count / len(records) * 100, 1),
        "avg_confidence": round(total_conf / len(records), 3),
    }


def update_learning_feedback(record_id: int, was_correct: bool, feedback: str = ""):
    """Update a learning record with human feedback."""
    conn = _get_conn()
    conn.execute(
        "UPDATE learning_records SET was_correct = ?, feedback = ? WHERE id = ?",
        (1 if was_correct else 0, feedback, record_id)
    )
    conn.commit()


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict, parsing JSON fields."""
    d = dict(row)
    for field in ("details", "metrics_snapshot", "rca_result", "remediation_result"):
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d
