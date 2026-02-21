"""
Knowledge Base — Loads incident knowledge from data/knowledge.json.

Provides lookup functions for incident patterns, remediation steps,
severity mapping, and risk weights.
"""

import json
import os

_KB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "knowledge.json")
_knowledge: dict | None = None


def _load() -> dict:
    """Lazy-load and cache the knowledge base."""
    global _knowledge
    if _knowledge is None:
        with open(_KB_PATH, "r", encoding="utf-8") as f:
            _knowledge = json.load(f)
    return _knowledge


def get_incident_pattern(incident_type: str) -> dict | None:
    """Return the full knowledge entry for an incident type."""
    kb = _load()
    return kb.get("incident_patterns", {}).get(incident_type)


def get_common_causes(incident_type: str) -> list[str]:
    """Return known common causes for an incident type."""
    pattern = get_incident_pattern(incident_type)
    return pattern.get("common_causes", []) if pattern else []


def get_remediation_steps(incident_type: str) -> list[str]:
    """Return ordered remediation steps for an incident type."""
    pattern = get_incident_pattern(incident_type)
    return pattern.get("remediation_steps", []) if pattern else []


def get_remediation_endpoint(incident_type: str) -> str | None:
    """Return the service remediation endpoint."""
    pattern = get_incident_pattern(incident_type)
    return pattern.get("remediation_endpoint") if pattern else None


def get_risk_weight(incident_type: str) -> float:
    """Return the risk weight (0-1) for an incident type."""
    pattern = get_incident_pattern(incident_type)
    return pattern.get("risk_weight", 0.5) if pattern else 0.5


def get_severity(incident_type: str, metrics: dict) -> str:
    """
    Determine severity level based on incident type and current metrics.

    Returns: 'low', 'medium', 'high', or 'critical'
    """
    pattern = get_incident_pattern(incident_type)
    if not pattern:
        return "medium"

    sev_map = pattern.get("severity_map", {})

    if incident_type == "CRASH":
        return "critical"

    if incident_type in ("MEMORY_LEAK",):
        value = metrics.get("memory_percent", 0)
        for level, criteria in sev_map.items():
            mem_range = criteria.get("memory_range", [0, 0])
            if mem_range[0] <= value < mem_range[1]:
                return level

    if incident_type in ("CPU_SPIKE",):
        value = metrics.get("cpu_percent", 0)
        for level, criteria in sev_map.items():
            cpu_range = criteria.get("cpu_range", [0, 0])
            if cpu_range[0] <= value < cpu_range[1]:
                return level

    if incident_type in ("DB_OVERLOAD", "LATENCY_SPIKE"):
        # Use latency if available, else default medium
        return "medium"

    return "medium"


def get_expected_recovery_time(incident_type: str) -> int:
    """Return expected recovery time in seconds."""
    pattern = get_incident_pattern(incident_type)
    return pattern.get("expected_recovery_time_s", 15) if pattern else 15


def get_escalation_rules() -> dict:
    """Return escalation configuration."""
    kb = _load()
    return kb.get("escalation_rules", {})


def get_risk_thresholds() -> dict:
    """Return risk threshold ranges."""
    kb = _load()
    return kb.get("risk_thresholds", {})


def get_all_incident_types() -> list[str]:
    """Return all known incident types."""
    kb = _load()
    return list(kb.get("incident_patterns", {}).keys())
