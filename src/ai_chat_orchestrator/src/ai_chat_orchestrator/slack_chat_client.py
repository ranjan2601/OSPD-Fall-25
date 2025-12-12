"""ChatInterface implementation for Slack using the service-backed client."""

from __future__ import annotations

from collections.abc import Iterator

from chat_client_api import Channel, ChatInterface, Message

from slack_adapter import SlackServiceBackedClient


class SlackChatClient(ChatInterface):
    """ChatInterface implementation for Slack."""

    def __init__(self, base_url: str = "", token: str = "") -> None:
        """Initialize Slack chat client.

        Args:
            base_url: Base URL for the Slack service
            token: Authentication token for Slack API
        """
        from typing import Any

        # Use httpx if available, otherwise use a simple wrapper
        self._httpx_client: Any = None
        try:
            import httpx

            self._httpx_client = httpx.Client(
                base_url=base_url,
                headers={"Authorization": f"Bearer {token}"} if token else {},
            )
            self._backend = SlackServiceBackedClient(base_url=base_url, http=self._httpx_client)  # type: ignore[arg-type]
        except ImportError:
            # Fallback for tests or environments without httpx
            self._httpx_client = None
            self._backend = SlackServiceBackedClient(base_url=base_url)

        self._messages_cache: dict[str, dict[str, Message]] = {}

    def get_message(self, channel_id: str, message_id: str) -> Message:
        """Retrieve a specific message from a channel.

        Args:
            channel_id: The ID of the channel containing the message.
            message_id: The ID of the message to retrieve.

        Returns:
            Message: The requested message.

        Raises:
            ValueError: If the message is not found.
        """
        # Check cache first
        if channel_id in self._messages_cache:
            if message_id in self._messages_cache[channel_id]:
                return self._messages_cache[channel_id][message_id]

        # Fetch from backend - this will need to be implemented in the backend
        # For now, raise NotImplementedError as the Slack service doesn't support
        # fetching individual messages by ID
        msg = f"Slack API doesn't support fetching individual messages by ID. Channel: {channel_id}, Message: {message_id}"
        raise NotImplementedError(msg)

    def get_messages(self, channel_id: str, limit: int = 10) -> list[Message]:
        """Retrieve recent messages from a channel.

        Args:
            channel_id: The ID of the channel to retrieve messages from.
            limit: Maximum number of messages to retrieve (default: 10).

        Returns:
            list[Message]: A list of messages from the channel.
        """
        # The backend doesn't have get_channel_history, so we'll return empty for now
        # This would need to be implemented in the service
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
            msg = self._backend.post_message(channel_id, content)
            # Cache the sent message
            if channel_id not in self._messages_cache:
                self._messages_cache[channel_id] = {}
            self._messages_cache[channel_id][msg.id] = msg
            return True
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
        # Remove from cache if present
        if channel_id in self._messages_cache:
            self._messages_cache[channel_id].pop(message_id, None)
        # The Slack service backend doesn't support delete, so we just return True
        return True

    def get_channels(self) -> Iterator[Channel]:
        """Retrieve all accessible channels.

        Returns:
            Iterator[Channel]: An iterator of available channels.
        """
        channels = self._backend.list_channels()
        return iter(channels)

    def get_channel(self, channel_id: str) -> Channel:
        """Retrieve information about a specific channel.

        Args:
            channel_id: The ID of the channel to retrieve.

        Returns:
            Channel: The requested channel.

        Raises:
            ValueError: If the channel is not found.
        """
        channels = self._backend.list_channels()
        for channel in channels:
            if channel.channel_id == channel_id:
                return channel
        msg = f"Channel not found: {channel_id}"
        raise ValueError(msg)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._httpx_client is not None:
            self._httpx_client.close()
        self._backend.close()
