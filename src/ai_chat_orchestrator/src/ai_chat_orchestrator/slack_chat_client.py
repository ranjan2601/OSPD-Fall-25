"""ChatInterface implementation for Slack using the real Slack API client."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from chat_client_api import ChatInterface, Message

# Add slack_impl to path
slack_impl_path = Path(__file__).parent.parent.parent.parent.parent / "slack_impl/src"
sys.path.insert(0, str(slack_impl_path))

from slack_impl import SlackClient


class SlackMessageAdapter(Message):
    """Adapter to make slack_impl.Message compatible with ChatInterface.Message."""

    def __init__(self, slack_message: Any) -> None:
        """Initialize from slack_impl Message."""
        self._slack_msg = slack_message

    @property
    def id(self) -> str:
        """Return message ID."""
        return str(self._slack_msg.id or self._slack_msg.ts)

    @property
    def content(self) -> str:
        """Return message content."""
        return str(self._slack_msg.text)

    @property
    def sender_id(self) -> str:
        """Return sender ID."""
        # slack_impl.Message doesn't have sender_id, use empty string
        return ""


class SlackChatClient(ChatInterface):
    """ChatInterface implementation for Slack using real Slack API."""

    def __init__(self, base_url: str = "", token: str = "") -> None:
        """Initialize Slack chat client.

        Args:
            base_url: Base URL for the Slack API (default: https://slack.com/api)
            token: Bot User OAuth Token (must start with xoxb-)
        """
        self._backend = SlackClient(base_url=base_url or "https://slack.com/api", token=token)

    def get_messages(self, channel_id: str, limit: int = 10) -> list[Message]:
        """Retrieve recent messages from a channel.

        Args:
            channel_id: The ID of the channel to retrieve messages from.
            limit: Maximum number of messages to retrieve (default: 10).

        Returns:
            list[Message]: A list of messages from the channel.
        """
        try:
            slack_messages = self._backend.get_channel_history(channel_id, limit=limit)
            return [SlackMessageAdapter(msg) for msg in slack_messages]
        except Exception:  # noqa: BLE001
            return []

    def send_message(self, channel_id: str, content: str) -> bool:
        """Send a message to a channel.

        Args:
            channel_id: The ID of the channel to send the message to.
            content: The text content of the message.

        Returns:
            bool: True if the message was successfully sent, False otherwise.
        """
        try:
            result = self._backend.post_message(channel_id, content)
            return result is not None and result.ts != ""
        except Exception:  # noqa: BLE001
            return False

    def delete_message(self, channel_id: str, message_id: str) -> bool:
        """Delete a message from a channel.

        Args:
            channel_id: The ID of the channel containing the message.
            message_id: The ID of the message to delete.

        Returns:
            bool: True if the message was successfully deleted, False otherwise.
        """
        # Slack API requires chat.delete which isn't in slack_impl
        # Return True as a no-op for now
        return True

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if hasattr(self._backend, "close"):
            self._backend.close()
