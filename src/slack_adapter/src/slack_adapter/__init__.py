"""Public API surface for the slack_adapter package."""

from __future__ import annotations

from chat_client_api import Channel, Message

from .adapter import (
    ServiceAdapter,
    ServiceBackedClient,
    SlackMessage,
    SlackServiceBackedClient,
    _get_id,
)

# Explicit public API (sorted for Ruff RUF022)
__all__ = [
    "Channel",
    "Message",
    "ServiceAdapter",
    "ServiceBackedClient",
    "SlackMessage",
    "SlackServiceBackedClient",
    "_get_id",
]
