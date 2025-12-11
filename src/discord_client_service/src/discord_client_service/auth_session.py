"""Simple server-side state and session store for OAuth flow.

This is intentionally minimal and stores state and sessions in-memory.
For production, replace with Redis or a durable store.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from fastapi import Cookie, HTTPException

# In-memory stores. Keys are hex strings.
_STATE_STORE: dict[str, dict[str, Any]] = {}
_SESSION_STORE: dict[str, dict[str, Any]] = {}
# Credentials store (in-memory): maps guild_id -> credential dict
_CREDENTIAL_STORE: dict[str, dict[str, Any]] = {}

# TTLs in seconds
STATE_TTL = 300  # 5 minutes for OAuth state
SESSION_TTL = 3600  # 1 hour for session


def _now() -> float:
    return time.time()


def create_state(guild_id: str | None) -> str:
    """Create and store a state value tied to a guild_id (may be None)."""
    s = uuid.uuid4().hex
    _STATE_STORE[s] = {"guild_id": guild_id, "created": _now()}
    return s


def pop_state(state: str) -> dict[str, Any] | None:
    """Consume a state value atomically. Returns stored dict or None."""
    entry = _STATE_STORE.pop(state, None)
    if not entry:
        return None
    if _now() - entry.get("created", 0) > STATE_TTL:
        return None
    return entry


def create_session(allowed_guilds: list[str]) -> str:
    """Create a session mapping and return session id."""
    sid = uuid.uuid4().hex
    _SESSION_STORE[sid] = {"guilds": list(allowed_guilds), "created": _now()}
    return sid


async def set_credential(guild_id: str, credential: dict[str, Any]) -> None:
    """Store credential dict for a guild (in-memory)."""
    _CREDENTIAL_STORE[guild_id] = dict(credential)


async def get_credential(guild_id: str) -> dict[str, Any] | None:
    """Retrieve stored credential dict for a guild, or None if missing."""
    return _CREDENTIAL_STORE.get(guild_id)


async def delete_credential(guild_id: str) -> bool:
    """Delete stored credential for a guild. Returns True if deleted."""
    if guild_id in _CREDENTIAL_STORE:
        _CREDENTIAL_STORE.pop(guild_id, None)
        return True
    return False


def check_session(session_id: str | None, guild_id: str) -> bool:
    """Return True if session_id exists, is not expired, and includes guild_id."""
    if not session_id:
        return False
    s = _SESSION_STORE.get(session_id)
    if not s:
        return False
    if _now() - s.get("created", 0) > SESSION_TTL:
        # expired
        _SESSION_STORE.pop(session_id, None)
        return False
    return guild_id in s.get("guilds", [])


def require_guild_access(guild_id: str, session_id: str | None = Cookie(None)) -> None:
    """FastAPI dependency to enforce the session contains the guild_id.

    Raises HTTPException(403) when access is not allowed.
    """
    if not check_session(session_id, guild_id):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: session does not allow access to this guild",
        )
