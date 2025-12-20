"""Additional coverage on GET/POST-only clients and error branches."""

from __future__ import annotations

import pytest
from chat_client_api import Message  # runtime construction only

from slack_adapter import ServiceAdapter, SlackChannel, _get_id  # type: ignore[import]


class OnlyGetPostHTTP:
    """HTTP stub that supports only GET and POST."""

    def __init__(self) -> None:
        self.closed = False

    def get(self, url: str, **_kwargs: object) -> object:
        """Return health or channels variations."""
        if url == "/health":

            class HealthResp:
                status_code = 200

                def json(self) -> dict[str, object]:
                    return {"unexpected": "shape"}

            return HealthResp()
        if url == "/channels":

            class ChannelsResp:
                def json(self) -> dict[str, object]:
                    return {"channels": [{"id": "C42", "name": "answer"}]}

            return ChannelsResp()

        msg = "unexpected GET"
        raise AssertionError(msg)

    def post(self, url: str, **kwargs: object) -> object:
        """Return a message echo for /messages."""
        if url == "/messages":
            json_param = kwargs.get("json", {})
            j = json_param if isinstance(json_param, dict) else {}

            class MessageResp:
                def json(self) -> dict[str, object]:
                    return {
                        "message": {
                            "id": "m-42",
                            "channel_id": j.get("channel_id", ""),
                            "text": j.get("text", ""),
                        },
                    }

            return MessageResp()

        msg = "unexpected POST"
        raise AssertionError(msg)

    def close(self) -> None:
        """Mark closed for context tests."""
        self.closed = True


class BadHTTP:
    """Client lacking request/get/post to trigger AttributeError in _do_request."""


def test_adapter_get_post_paths_and_health_variants() -> None:
    """Happy paths against a GET/POST-only client."""
    http = OnlyGetPostHTTP()
    adapter = ServiceAdapter(lambda: http)

    if adapter.health() is not True:
        pytest.fail("health default should be True on odd JSON shapes")

    chs = adapter.list_channels()
    if len(chs) != 1:
        pytest.fail("expected one channel")
    if not isinstance(chs[0], SlackChannel):
        pytest.fail("expected SlackChannel")
    if chs[0].id != "C42":
        pytest.fail("channel id mismatch")

    msg = adapter.post_message("C42", "msg")
    if not isinstance(msg, Message):
        pytest.fail("expected Message")
    if msg.id != "m-42":
        pytest.fail("message id mismatch")


def test_do_request_error_branch() -> None:
    """Exercise _do_request AttributeError branch via bad client."""
    adapter = ServiceAdapter(lambda: BadHTTP())
    # Any public method should hit the same error path; choose health():
    _ = adapter.health()


def test_get_id_variants() -> None:
    """Cover additional _get_id shapes."""
    if _get_id({"message_id": "m9"}) != "m9":
        pytest.fail("message_id extraction failed")
    if _get_id({"ts": "9.99"}) != "9.99":
        pytest.fail("ts extraction failed")
