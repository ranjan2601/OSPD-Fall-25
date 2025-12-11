"""Tests for auth_session in-memory helpers."""

import time

import pytest
from fastapi import HTTPException

from discord_client_service import auth_session


def test_create_and_pop_state_and_ttl() -> None:
    """Create a state for a guild, pop it and ensure it is returned only once."""
    s = auth_session.create_state("g1")
    assert isinstance(s, str)
    entry = auth_session.pop_state(s)
    assert entry is not None
    assert entry.get("guild_id") == "g1"

    # pop again -> None
    assert auth_session.pop_state(s) is None


def test_pop_state_expired(monkeypatch: "pytest.MonkeyPatch") -> None:
    """A state older than STATE_TTL is treated as expired and returns None."""
    # create a state at 'now'
    now = time.time()
    s = auth_session.create_state("g2")
    # make time.time() appear to have advanced beyond the TTL so pop_state sees it as expired
    monkeypatch.setattr(time, "time", lambda: now + auth_session.STATE_TTL + 10)
    assert auth_session.pop_state(s) is None


@pytest.mark.asyncio
async def test_credentials_set_get_delete() -> None:
    """Set, get and delete credentials for a guild."""
    await auth_session.set_credential("g1", {"a": 1})
    got = await auth_session.get_credential("g1")
    # mypy: get_credential() returns Optional[...] so assert non-None before indexing
    assert got is not None
    assert got["a"] == 1
    deleted = await auth_session.delete_credential("g1")
    assert deleted is True
    assert await auth_session.get_credential("g1") is None


def test_create_session_and_check_and_expiry(monkeypatch: "pytest.MonkeyPatch") -> None:
    """Create a session, check access, and ensure it expires after SESSION_TTL."""
    sid = auth_session.create_session(["g1"])
    assert auth_session.check_session(sid, "g1") is True

    # simulate time passing beyond SESSION_TTL so check_session returns False
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now + auth_session.SESSION_TTL + 1)
    assert auth_session.check_session(sid, "g1") is False


def test_require_guild_access_forbidden() -> None:
    """require_guild_access raises HTTPException when session is missing/invalid."""
    with pytest.raises(HTTPException):
        auth_session.require_guild_access("g1", None)


def test_check_session_none_and_missing() -> None:
    """check_session returns False for None or unknown session ids."""
    # session id None should be false
    assert auth_session.check_session(None, "g1") is False
    # random id not present
    assert auth_session.check_session("no-such-id", "g1") is False
