"""Coverage-oriented tests for adapter request paths and helpers."""

from __future__ import annotations

import pytest
from chat_client_api import Message  # only for runtime construction

from slack_adapter import (
    ServiceAdapter,
    ServiceBackedClient,
    SlackChannel,
    SlackMessage,
    _get_id,
)  # type: ignore[import]


class DummyHTTPXClient:
    """Unified `request()` client returning small structs that look like responses."""

    def __init__(self) -> None:
        """Track close() calls for context-manager coverage."""
        self.closed = False

    def request(  # noqa: PLR0913
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,  # noqa: ARG002
        json: dict[str, object] | None = None,
        headers: dict[str, str] | None = None,  # noqa: ARG002
        timeout: float | None = None,  # noqa: ARG002
    ) -> object:
        """Return an object with attributes accessed by the adapter.

        Health: {"ok": True}
        /channels: {"channels": [{"id": "C9", "name": "gen"}]}
        /messages: echoes json payload back into {"message": {...}}
        """

        class R:
            def __init__(
                self,
                method: str,
                url: str,
                json_data: dict[str, object] | None,
            ) -> None:
                self.method = method
                self.url = url
                self.json_data = json_data
                self.status_code = 200

            def json(self) -> dict[str, object]:
                if self.url == "/health":
                    return {"ok": True}
                if self.url == "/channels":
                    return {"channels": [{"id": "C9", "name": "gen"}]}
                if self.url == "/messages":
                    j = self.json_data or {}
                    return {
                        "message": {
                            "id": "m-1",
                            "channel_id": j.get("channel_id", ""),
                            "text": j.get("text", ""),
                        },
                    }
                return {}

        return R(method, url, json)

    def close(self) -> None:
        """Mark the client as closed."""
        self.closed = True


def test_health_list_and_post_paths() -> None:
    """Happy paths for health, channels, and posting message."""
    http = DummyHTTPXClient()
    adapter = ServiceAdapter(lambda: http)

    if adapter.health() is not True:
        pytest.fail("health should be True")

    chs = adapter.list_channels()
    if len(chs) != 1:
        pytest.fail("expected exactly one channel")
    if not isinstance(chs[0], SlackChannel):
        pytest.fail("expected a SlackChannel instance")
    if chs[0].id != "C9":
        pytest.fail("channel id mismatch")

    msg = adapter.post_message("C9", "hello")
    if not isinstance(msg, Message):
        pytest.fail("expected a Message instance")
    if msg.channel_id != "C9":
        pytest.fail("message channel_id mismatch")
    if msg.id != "m-1":
        pytest.fail("message id mismatch")


def test_get_id_and_public_client_close_and_identifier() -> None:
    """Cover _get_id variants, message_identifier, and context mgmt."""
    http = DummyHTTPXClient()
    client = ServiceBackedClient(base_url="http://test", http=http)  # type: ignore[arg-type]

    if _get_id({"id": "x"}) != "x":
        pytest.fail("_get_id did not return 'id'")
    if (
        _get_id(
            SlackMessage(
                _id="m2",
                _content="t",
                _channel_id="c",
                _sender_id="u1",
                _timestamp="1.0",
            ),
        )
        != "m2"
    ):
        pytest.fail("_get_id did not extract message_id from SlackMessage")

    if client.message_identifier({"id": "ok"}) != "ok":
        pytest.fail("message_identifier happy path failed")

    try:
        client.message_identifier({"bad": "shape"})
    except ValueError:
        pass
    else:
        pytest.fail("expected ValueError for bad message shape")

    with client as c2:
        if c2 is not client:
            pytest.fail("__enter__ did not return self")
    if http.closed is not True:
        pytest.fail("HTTP client was not closed after context exit")
