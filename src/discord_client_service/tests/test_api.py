"""Unit tests for the discord_client_service FastAPI API.

These tests mirror the style used for the mail client service tests and use
fake client implementations to exercise the HTTP routes without external
dependencies.
"""

from collections.abc import Callable, Generator
from importlib import util
from pathlib import Path
from typing import Any, cast

# Module-level constants and imports.
import pytest
from fastapi.testclient import TestClient

from discord_client_service import api, service

# Attempt to import the auth dependency at module import time so linters
# see the import at top-level. If the import isn't available in some test
# contexts, set to None and handle below. Declare an explicit annotated
# optional type so mypy understands the variable may be None.
require_guild_access: Callable[..., Any] | None = None
try:
    # import under a temporary name then assign to the annotated name so
    # mypy keeps the declared Optional type on `require_guild_access`.
    from discord_client_service.auth_session import require_guild_access as _require_guild_access

    require_guild_access = _require_guild_access
except ImportError:
    require_guild_access = None

# Load the sibling test helper module (works whether pytest imports tests as
# modules or as plain files). This avoids relative import issues during
# test collection when running a subset of tests.
spec = util.spec_from_file_location(
    "test_fake_discord", Path(__file__).with_name("test_fake_discord.py")
)
assert spec is not None
assert spec.loader is not None
test_fake = util.module_from_spec(spec)
assert test_fake is not None
spec.loader.exec_module(test_fake)

FakeBotClient = test_fake.FakeBotClient
FakeUserClient = test_fake.FakeUserClient
FakeChannel = test_fake.FakeChannel
FakeMessage = test_fake.FakeMessage

# Use constants to avoid magic numbers in tests
HTTP_OK = 200
HTTP_NOT_FOUND = 404
EXPECTED_CHANNEL_COUNT = 1
EXPECTED_MESSAGE_COUNT = 2


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient with auth dependency overridden and fake clients patched in."""
    # Override auth dependency so tests don't need real sessions/cookies
    if require_guild_access is not None:

        async def _no_auth() -> None:  # async to match possible async dependency
            return None

        service.app.dependency_overrides[require_guild_access] = _no_auth

    # Patch helper functions and DiscordClient class used in the API module so
    # routes call our fakes.
    fake_user_client = FakeUserClient()
    fake_bot_client = FakeBotClient(channels=[FakeChannel("c1", "general")])

    # Replace resolution functions used by the api module
    async def _get_client_for_user(_guild_id: str) -> object:
        return fake_user_client

    async def _get_bot_client_for_guild(_guild_id: str) -> object:
        return fake_bot_client

    async def _check_user_authenticated(_guild_id: str) -> bool:
        return True

    async def _delete_user_credentials(_guild_id: str) -> bool:
        return True

    # Use setattr on a cast-to-Any module to avoid mypy errors about
    # attributes that the real `api` module may not export in its __all__
    # and to bypass strict type checks for the fake callables we inject.
    cast("Any", api).get_client_for_user = _get_client_for_user
    cast("Any", api).get_bot_client_for_guild = _get_bot_client_for_guild
    cast("Any", api).check_user_authenticated = _check_user_authenticated
    cast("Any", api).delete_user_credentials = _delete_user_credentials

    # Provide a fake DiscordClient for oauth login path
    class _FakeDiscordClient:
        def _get_authorization_url(self, _state: str | None = None) -> tuple[str, str]:
            return ("http://auth.example/authorize", "state123")

    cast("Any", api).DiscordClient = _FakeDiscordClient

    test_client = TestClient(service.app)
    yield test_client
    service.app.dependency_overrides.clear()


@pytest.mark.unit
def test_health_check(client: TestClient) -> None:
    """Health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == HTTP_OK
    assert response.json()["status"] == "healthy"


@pytest.mark.unit
def test_oauth_login_returns_url(client: TestClient) -> None:
    """OAuth login returns an authorization URL and state."""
    response = client.get("/auth/login")
    assert response.status_code == HTTP_OK
    data = response.json()
    assert "authorization_url" in data
    assert data["authorization_url"].startswith("http")


@pytest.mark.unit
def test_get_channels_success(client: TestClient) -> None:
    """List channels for a guild returns expected channel list."""
    response = client.get("/guilds/g1/channels")
    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["count"] == EXPECTED_CHANNEL_COUNT
    assert data["channels"][0]["name"] == "general"


@pytest.mark.unit
def test_get_channel_success(client: TestClient) -> None:
    """Retrieve a single channel by id returns channel details."""
    response = client.get("/g1/channels/c1")
    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["id"] == "c1"
    assert data["name"] == "general"


@pytest.mark.unit
def test_get_messages_success(client: TestClient) -> None:
    """Retrieve messages from a channel returns expected messages."""
    response = client.get("/g1/channels/c1/messages")
    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["count"] == EXPECTED_MESSAGE_COUNT
    assert data["messages"][0]["content"] == "first"


@pytest.mark.unit
def test_send_message_success(client: TestClient) -> None:
    """Sending a message returns the sent message payload."""
    response = client.post("/g1/channels/c1/messages", json={"content": "hi there"})
    assert response.status_code == HTTP_OK


@pytest.mark.unit
def test_delete_message_success(client: TestClient) -> None:
    """Deleting an existing message returns success status."""
    # ensure message exists then delete
    response = client.delete("/g1/channels/c1/messages/m1")
    assert response.status_code == HTTP_OK
    assert response.json()["status"] == "success"


@pytest.mark.unit
def test_delete_message_not_found(client: TestClient) -> None:
    """Deleting a non-existent message returns a 404 status."""
    response = client.delete("/g1/channels/c1/messages/does-not-exist")
    assert response.status_code == HTTP_NOT_FOUND


@pytest.mark.unit
def test_auth_status(client: TestClient) -> None:
    """Auth status endpoint indicates whether user is authenticated."""
    response = client.get("/auth/status/g1")
    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["authenticated"] is True


@pytest.mark.unit
def test_oauth_logout_success(client: TestClient) -> None:
    """Logging out via OAuth deletes credentials and returns success."""
    response = client.delete("/auth/logout/g1")
    assert response.status_code == HTTP_OK
    data = response.json()
    assert data["status"] == "success"
