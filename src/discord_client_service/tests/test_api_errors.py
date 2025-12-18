"""Additional tests to exercise error branches in api.py."""

from collections.abc import Callable, Iterator
from typing import Any, NoReturn

import pytest
from chat_client_api.exceptions import MessageDeleteError
from fastapi.testclient import TestClient

from discord_client_service import api, service

# short alias for pytest.MonkeyPatch to keep function signatures under 100 chars
MP = pytest.MonkeyPatch

# HTTP status constants to avoid magic numbers in assertions
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500


# `require_guild_access` may not exist in some test environments; declare it
# Optional so mypy accepts the `None` fallback below.
require_guild_access: Callable[..., Any] | None
try:
    # import under a temporary name to preserve the annotated name
    from discord_client_service.auth_session import require_guild_access as _require_guild_access

    require_guild_access = _require_guild_access
except (ImportError, ModuleNotFoundError):
    require_guild_access = None


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Test client fixture with auth dependency overridden."""
    # override auth dependency if available
    if require_guild_access is not None:

        async def _no_auth() -> None:
            return None

        service.app.dependency_overrides[require_guild_access] = _no_auth

    test_client = TestClient(service.app)
    yield test_client
    service.app.dependency_overrides.clear()


@pytest.mark.unit
def test_oauth_login_exception(client: TestClient, monkeypatch: MP) -> None:
    """Discord OAuth login errors map to 500."""

    class BadClient:
        def _get_authorization_url(self, _state: str | None = None) -> NoReturn:
            msg = "boom"
            raise RuntimeError(msg)

    monkeypatch.setattr(api, "DiscordClient", BadClient)
    r = client.get("/auth/login")
    assert r.status_code == HTTP_INTERNAL_SERVER_ERROR


@pytest.mark.unit
def test_oauth_callback_missing_guild(monkeypatch: MP, client: TestClient) -> None:
    """Missing guild in callback results in 400."""

    class C:
        def _exchange_code_for_token(self, _code: str) -> dict[str, str]:
            return {"access_token": "t"}

    monkeypatch.setattr(api, "DiscordClient", C)
    # pop_state returns None by default; do not provide guild_id
    r = client.get("/auth/callback?code=abc")
    assert r.status_code == HTTP_BAD_REQUEST


@pytest.mark.unit
def test_oauth_callback_exchange_error(monkeypatch: MP, client: TestClient) -> None:
    """Token exchange failures return 500."""

    class C:
        def _exchange_code_for_token(self, _code: str) -> NoReturn:
            msg = "fail exchange"
            raise RuntimeError(msg)

    monkeypatch.setattr(api, "DiscordClient", C)
    r = client.get("/auth/callback?code=abc&guild_id=g1")
    assert r.status_code == HTTP_INTERNAL_SERVER_ERROR


@pytest.mark.unit
def test_oauth_callback_success(monkeypatch: MP, client: TestClient) -> None:
    """Successful callback sets a session cookie."""

    # Successful token exchange and credential storage should set a session cookie
    class C:
        def _exchange_code_for_token(self, _code: str) -> dict[str, str]:
            return {"access_token": "t"}

    # stored will hold both string fields and a token dict; widen the value type
    stored: dict[str, Any] = {}

    async def _store_user_credentials(guild_id: str, token_data: dict[str, str]) -> None:
        stored["guild_id"] = guild_id
        stored["token"] = token_data

    monkeypatch.setattr(api, "DiscordClient", C)
    monkeypatch.setattr(api, "store_user_credentials", _store_user_credentials)
    # Use guild_id query param to avoid needing server-side state
    # Some TestClient versions do not accept `allow_redirects`; rely on default
    # behavior and verify cookie presence on the final response.
    r = client.get("/auth/callback?code=abc&guild_id=g1")
    # RedirectResponse may be followed by TestClient; allow final 200 as well
    assert r.status_code in (200, 301, 302, 303, 307, 308)
    # Different TestClient versions expose cookies on the response or the
    # client's cookie jar. Accept either location for compatibility.
    assert ("session_id" in r.cookies) or ("session_id" in client.cookies)


@pytest.mark.unit
def test_oauth_logout_not_found(monkeypatch: MP, client: TestClient) -> None:
    """If credential deletion reports not found, 404 is returned."""

    async def _delete_user_credentials(_guild_id: str) -> bool:
        return False

    monkeypatch.setattr(api, "delete_user_credentials", _delete_user_credentials)
    r = client.delete("/auth/logout/g1")
    assert r.status_code == HTTP_NOT_FOUND


@pytest.mark.unit
def test_oauth_logout_bot_leave_failure(monkeypatch: MP, client: TestClient) -> None:
    """Bot client errors during leave are surfaced as 200 logout success."""

    async def _delete_user_credentials(_gid: str) -> bool:
        return True

    class Bot:
        def leave_guild(self, _gid: str) -> NoReturn:
            msg = "leave failed"
            raise RuntimeError(msg)

    async def _get_bot_client_for_guild(_gid: str) -> object:
        return Bot()

    monkeypatch.setattr(api, "delete_user_credentials", _delete_user_credentials)
    monkeypatch.setattr(api, "get_bot_client_for_guild", _get_bot_client_for_guild)
    r = client.delete("/auth/logout/g1")
    assert r.status_code == HTTP_OK


@pytest.mark.unit
def test_get_channels_unauth(monkeypatch: MP, client: TestClient) -> None:
    """Unauthorized channel listing returns 401."""

    async def _gb(_gid: str) -> NoReturn:
        msg = "not authenticated"
        raise ValueError(msg)

    monkeypatch.setattr(api, "get_bot_client_for_guild", _gb)
    r = client.get("/guilds/g1/channels")
    assert r.status_code == HTTP_UNAUTHORIZED


@pytest.mark.unit
def test_get_channels_error(monkeypatch: MP, client: TestClient) -> None:
    """Server errors while listing channels return 500."""

    async def _gb(_gid: str) -> NoReturn:
        msg = "oh"
        raise RuntimeError(msg)

    monkeypatch.setattr(api, "get_bot_client_for_guild", _gb)
    r = client.get("/guilds/g1/channels")
    assert r.status_code == HTTP_INTERNAL_SERVER_ERROR


@pytest.mark.unit
def test_get_channel_not_found(monkeypatch: MP, client: TestClient) -> None:
    """Missing channel maps to 404."""

    async def _gc(_gid: str) -> NoReturn:
        msg = "not found"
        raise ValueError(msg)

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c99")
    assert r.status_code == HTTP_NOT_FOUND


@pytest.mark.unit
def test_get_channel_unauth(monkeypatch: MP, client: TestClient) -> None:
    """Unauthorized channel access returns 401."""

    async def _gc(_gid: str) -> NoReturn:
        msg = "no auth"
        raise ValueError(msg)

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c1")
    assert r.status_code == HTTP_UNAUTHORIZED


@pytest.mark.unit
def test_get_channel_error(monkeypatch: MP, client: TestClient) -> None:
    """Unexpected errors while getting a channel return 500."""

    async def _gc(_gid: str) -> NoReturn:
        msg = "bad"
        raise RuntimeError(msg)

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c1")
    assert r.status_code == HTTP_INTERNAL_SERVER_ERROR


@pytest.mark.unit
def test_get_messages_unauth(monkeypatch: MP, client: TestClient) -> None:
    """Unauthorized message fetch returns 401."""

    async def _gc(_gid: str) -> NoReturn:
        msg = "auth"
        raise ValueError(msg)

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c1/messages")
    assert r.status_code == HTTP_UNAUTHORIZED


@pytest.mark.unit
def test_get_messages_error(monkeypatch: MP, client: TestClient) -> None:
    """General errors during messages fetch return 500."""

    async def _gc(_gid: str) -> NoReturn:
        msg = "boom"
        raise RuntimeError(msg)

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c1/messages")
    assert r.status_code == HTTP_INTERNAL_SERVER_ERROR


@pytest.mark.unit
def test_send_message_not_authenticated(monkeypatch: MP, client: TestClient) -> None:
    """Sending a message without authentication returns 401."""

    async def _gc(_gid: str) -> object:
        class C:
            def send_message(self, _channel_id: str, _content: str) -> NoReturn:
                msg = "not authenticated"
                raise ValueError(msg)

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.post("/g1/channels/c1/messages", json={"content": "x"})
    assert r.status_code == HTTP_UNAUTHORIZED


@pytest.mark.unit
def test_send_message_bad_request(monkeypatch: MP, client: TestClient) -> None:
    """Client-side send errors map to 400."""

    async def _gc(_gid: str) -> object:
        class C:
            def send_message(self, _channel_id: str, _content: str) -> NoReturn:
                msg = "other"
                raise ValueError(msg)

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.post("/g1/channels/c1/messages", json={"content": "x"})
    assert r.status_code == HTTP_BAD_REQUEST


@pytest.mark.unit
def test_send_message_error(monkeypatch: MP, client: TestClient) -> None:
    """Server-side send errors return 500."""

    async def _gc(_gid: str) -> object:
        class C:
            def send_message(self, _channel_id: str, _content: str) -> NoReturn:
                msg = "boom"
                raise RuntimeError(msg)

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.post("/g1/channels/c1/messages", json={"content": "x"})
    assert r.status_code == HTTP_INTERNAL_SERVER_ERROR


@pytest.mark.unit
def test_delete_message_delete_error(monkeypatch: MP, client: TestClient) -> None:
    """MessageDeleteError from client is translated to 500."""

    async def _gc(_gid: str) -> object:
        class C:
            def delete_message(self, _channel_id: str, _message_id: str) -> NoReturn:
                msg = "bad"
                raise MessageDeleteError(msg)

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.delete("/g1/channels/c1/messages/mx")
    assert r.status_code == HTTP_INTERNAL_SERVER_ERROR


@pytest.mark.unit
def test_delete_message_unauth(monkeypatch: MP, client: TestClient) -> None:
    """Unauthorized delete attempts return 401."""

    async def _gc(_gid: str) -> object:
        class C:
            def delete_message(self, _channel_id: str, _message_id: str) -> NoReturn:
                msg = "no auth"
                raise ValueError(msg)

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.delete("/g1/channels/c1/messages/mx")
    assert r.status_code == HTTP_UNAUTHORIZED


@pytest.mark.unit
def test_delete_message_error_general(monkeypatch: MP, client: TestClient) -> None:
    """Unexpected delete failures return 500."""

    async def _gc(_gid: str) -> object:
        class C:
            def delete_message(self, _channel_id: str, _message_id: str) -> NoReturn:
                msg = "boom"
                raise RuntimeError(msg)

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.delete("/g1/channels/c1/messages/mx")
    assert r.status_code == HTTP_INTERNAL_SERVER_ERROR
