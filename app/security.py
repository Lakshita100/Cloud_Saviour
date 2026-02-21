"""
Security Module — API key authentication, RBAC, and audit middleware.

Provides:
  - API key management (create, validate, revoke)
  - Role-based access control (admin, operator, viewer)
  - Request authentication middleware
  - Audit trail for every authenticated request
"""

import hashlib
import secrets
import json
import os
from datetime import datetime
from functools import wraps
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

# ──────────────────────────────────────────────
# API Key Storage (JSON file — simple & portable)
# ──────────────────────────────────────────────
_KEYS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "api_keys.json")
_api_keys: dict | None = None

# Roles and their permissions
ROLE_PERMISSIONS = {
    "admin": {
        "trigger_incident", "run_pipeline", "remediate", "restart",
        "view_dashboard", "manage_keys", "view_audit", "view_history",
        "give_feedback",
    },
    "operator": {
        "trigger_incident", "run_pipeline", "remediate", "restart",
        "view_dashboard", "view_audit", "view_history", "give_feedback",
    },
    "viewer": {
        "view_dashboard", "view_history",
    },
}

# Public endpoints that don't require auth
PUBLIC_ENDPOINTS = {
    "/", "/health", "/metrics", "/docs", "/openapi.json", "/redoc",
    "/favicon.ico",
}

# API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _hash_key(raw_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _load_keys() -> dict:
    """Load API keys from file."""
    global _api_keys
    if _api_keys is None:
        if os.path.exists(_KEYS_PATH):
            with open(_KEYS_PATH, "r", encoding="utf-8") as f:
                _api_keys = json.load(f)
        else:
            _api_keys = {"keys": {}}
            # Create a default admin key on first run
            _create_default_admin_key()
    return _api_keys


def _save_keys():
    """Persist API keys to disk."""
    os.makedirs(os.path.dirname(_KEYS_PATH), exist_ok=True)
    with open(_KEYS_PATH, "w", encoding="utf-8") as f:
        json.dump(_api_keys, f, indent=2)


def _create_default_admin_key():
    """Create a default admin API key on first startup."""
    global _api_keys
    raw_key = "cs-admin-" + secrets.token_hex(16)
    key_hash = _hash_key(raw_key)
    _api_keys["keys"][key_hash] = {
        "name": "default-admin",
        "role": "admin",
        "created_at": datetime.now().isoformat(),
        "revoked": False,
    }
    _api_keys["default_admin_key"] = raw_key  # stored ONCE for initial setup
    _save_keys()
    print(f"\n{'='*60}")
    print(f"  DEFAULT ADMIN API KEY (save this!):")
    print(f"  {raw_key}")
    print(f"{'='*60}\n")


def create_api_key(name: str, role: str = "viewer") -> str:
    """
    Create a new API key with the specified role.
    Returns the raw key (only shown once).
    """
    if role not in ROLE_PERMISSIONS:
        raise ValueError(f"Invalid role: {role}. Must be one of {list(ROLE_PERMISSIONS.keys())}")

    keys = _load_keys()
    raw_key = f"cs-{role[:3]}-" + secrets.token_hex(16)
    key_hash = _hash_key(raw_key)
    keys["keys"][key_hash] = {
        "name": name,
        "role": role,
        "created_at": datetime.now().isoformat(),
        "revoked": False,
    }
    _save_keys()
    return raw_key


def validate_api_key(raw_key: str) -> dict | None:
    """
    Validate an API key and return its metadata.
    Returns None if invalid or revoked.
    """
    keys = _load_keys()
    key_hash = _hash_key(raw_key)
    key_data = keys.get("keys", {}).get(key_hash)
    if key_data and not key_data.get("revoked", False):
        return key_data
    return None


def revoke_api_key(name: str) -> bool:
    """Revoke all API keys with the given name."""
    keys = _load_keys()
    revoked_any = False
    for key_hash, key_data in keys.get("keys", {}).items():
        if key_data.get("name") == name:
            key_data["revoked"] = True
            key_data["revoked_at"] = datetime.now().isoformat()
            revoked_any = True
    if revoked_any:
        _save_keys()
    return revoked_any


def list_api_keys() -> list[dict]:
    """List all API keys (without revealing the actual keys)."""
    keys = _load_keys()
    result = []
    for key_hash, key_data in keys.get("keys", {}).items():
        result.append({
            "name": key_data["name"],
            "role": key_data["role"],
            "created_at": key_data["created_at"],
            "revoked": key_data.get("revoked", False),
            "key_prefix": key_hash[:8] + "...",
        })
    return result


def has_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_default_admin_key() -> str | None:
    """
    Get the default admin key (only available in the keys file).
    Returns None if already consumed.
    """
    keys = _load_keys()
    return keys.get("default_admin_key")


# ──────────────────────────────────────────────
# FastAPI Authentication Dependency
# ──────────────────────────────────────────────

async def authenticate(request: Request, api_key: str = Security(api_key_header)) -> dict:
    """
    FastAPI dependency that validates the API key and returns key metadata.
    Used by protected endpoints.
    """
    # Allow public endpoints without auth
    if request.url.path in PUBLIC_ENDPOINTS:
        return {"name": "public", "role": "viewer"}

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include 'X-API-Key' header.",
        )

    key_data = validate_api_key(api_key)
    if not key_data:
        raise HTTPException(
            status_code=403,
            detail="Invalid or revoked API key.",
        )

    # Attach key info to request state for audit logging
    request.state.api_key_name = key_data["name"]
    request.state.api_key_role = key_data["role"]
    return key_data


def require_permission(permission: str):
    """
    Returns a FastAPI dependency that checks if the authenticated user
    has the required permission.
    """
    async def check(request: Request, key_data: dict = Security(authenticate)):
        if not has_permission(key_data["role"], permission):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {permission}, "
                       f"Your role: {key_data['role']}",
            )
        return key_data
    return check
