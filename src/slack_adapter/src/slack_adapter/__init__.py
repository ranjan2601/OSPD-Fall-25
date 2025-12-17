"""Public API surface for the slack_adapter package."""

from __future__ import annotations

from chat_client_api import Message

from .adapter import (
    ServiceAdapter,
    ServiceBackedClient,
    SlackChannel,
    SlackMessage,
    SlackServiceBackedClient,
    _get_id,
)

# Explicit public API (sorted for Ruff RUF022)
__all__ = [
    "Message",
    "ServiceAdapter",
    "ServiceBackedClient",
    "SlackChannel",
    "SlackMessage",
    "SlackServiceBackedClient",
    "_get_id",
]
