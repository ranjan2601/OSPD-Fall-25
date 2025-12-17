"""Coverage tests for discord_client_impl.auth_helper."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Any
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def auth_session_stub(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Install a stub `discord_client_service.auth_session` to avoid import cycles in tests."""

    svc = ModuleType("discord_client_service")
    auth = ModuleType("discord_client_service.auth_session")

    setattr(auth, "get_credential", AsyncMock(return_value=None))
    setattr(auth, "set_credential", AsyncMock(return_value=None))
    setattr(auth, "delete_credential", AsyncMock(return_value=False))

    sys.modules["discord_client_service"] = svc
    sys.modules["discord_client_service.auth_session"] = auth
    return auth


@pytest.mark.asyncio
async def test_get_client_for_user_no_credentials_raises(
    monkeypatch: pytest.MonkeyPatch, auth_session_stub: ModuleType
) -> None:
    from discord_client_impl import auth_helper
    importlib.reload(auth_helper)

    auth_session_stub.get_credential.return_value = None

    with pytest.raises(ValueError, match="No credentials found"):
        await auth_helper.get_client_for_user("guild1")


@pytest.mark.asyncio
async def test_get_client_for_user_uses_app_bot_token(
    monkeypatch: pytest.MonkeyPatch, auth_session_stub: ModuleType
) -> None:
    from discord_client_impl import auth_helper
    importlib.reload(auth_helper)

    monkeypatch.setenv("DISCORD_BOT_TOKEN", "bot-token")
    auth_session_stub.get_credential.return_value = {"access_token": "oauth-token", "token_type": "Bearer"}

    client = await auth_helper.get_client_for_user("guild1")
    assert client.access_token == "bot-token"
    assert client.token_type == "Bot"


@pytest.mark.asyncio
async def test_get_client_for_user_refreshes_expired_token(
    monkeypatch: pytest.MonkeyPatch, auth_session_stub: ModuleType
) -> None:
    from discord_client_impl import auth_helper
    importlib.reload(auth_helper)

    expires_at = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    auth_session_stub.get_credential.return_value = {
        "access_token": "old",
        "refresh_token": "rtok",
        "token_type": "Bearer",
        "expires_at": expires_at,
        "scope": "identify",
    }

    def _refresh(_self: Any, refresh_token: str) -> dict[str, object]:
        assert refresh_token == "rtok"
        return {
            "access_token": "new",
            "refresh_token": "newr",
            "token_type": "Bearer",
            "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "scope": "identify guilds",
        }

    from discord_client_impl.discord_impl import DiscordClient
    monkeypatch.setattr(DiscordClient, "_refresh_access_token", _refresh, raising=True)

    client = await auth_helper.get_client_for_user("guild1")
    assert client.access_token == "new"
    assert client.token_type == "Bearer"
    assert auth_session_stub.set_credential.await_count == 1


@pytest.mark.asyncio
async def test_get_client_for_user_expired_without_refresh_token(
    monkeypatch: pytest.MonkeyPatch, auth_session_stub: ModuleType
) -> None:
    from discord_client_impl import auth_helper
    importlib.reload(auth_helper)

    expires_at = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    auth_session_stub.get_credential.return_value = {"access_token": "old", "token_type": "Bearer", "expires_at": expires_at}

    # When refresh cannot happen, the helper logs and falls back to the stored token.
    client = await auth_helper.get_client_for_user("guild1")
    assert client.access_token == "old"


@pytest.mark.asyncio
async def test_get_client_for_user_bad_expires_at_falls_back(
    monkeypatch: pytest.MonkeyPatch, auth_session_stub: ModuleType
) -> None:
    from discord_client_impl import auth_helper
    importlib.reload(auth_helper)

    auth_session_stub.get_credential.return_value = {"access_token": "abc", "token_type": "Bearer", "expires_at": "not-a-date"}

    client = await auth_helper.get_client_for_user("guild1")
    assert client.access_token == "abc"
    assert client.token_type == "Bearer"


@pytest.mark.asyncio
async def test_get_bot_client_for_guild_env_and_store(
    monkeypatch: pytest.MonkeyPatch, auth_session_stub: ModuleType
) -> None:
    from discord_client_impl import auth_helper
    importlib.reload(auth_helper)

    monkeypatch.setenv("DISCORD_BOT_TOKEN", "env-bot")
    client = await auth_helper.get_bot_client_for_guild("guild1")
    assert client.access_token == "env-bot"

    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    auth_session_stub.get_credential.return_value = {"access_token": "stored-bot", "token_type": "Bot"}
    client2 = await auth_helper.get_bot_client_for_guild("guild1")
    assert client2.access_token == "stored-bot"
    assert client2.token_type == "Bot"


@pytest.mark.asyncio
async def test_delete_and_check_user_credentials(
    monkeypatch: pytest.MonkeyPatch, auth_session_stub: ModuleType
) -> None:
    from discord_client_impl import auth_helper
    importlib.reload(auth_helper)

    auth_session_stub.delete_credential.return_value = True
    assert await auth_helper.delete_user_credentials("guild1") is True

    auth_session_stub.get_credential.return_value = {"access_token": "x"}
    assert await auth_helper.check_user_authenticated("guild1") is True


