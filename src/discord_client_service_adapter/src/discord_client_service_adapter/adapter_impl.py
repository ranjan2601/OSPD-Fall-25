"""Service Adapter Implementation for Discord.

This module provides an adapter that implements the chat_client_api.ChatInterface interface
by wrapping the auto-generated OpenAPI client for the discord_client_service.

This demonstrates the Adapter Pattern: hiding network/HTTP complexity behind
a familiar local interface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import chat_client_api
from chat_client_api.message import Channel, Message
from discord_client_service_client import Client as GeneratedClient
from discord_client_service_client.api.default import (
    delete_message_guild_id_channels_channel_id_messages_message_id_delete,
    get_channel_guild_id_channels_channel_id_get,
    get_channels_guilds_guild_id_channels_get,
    get_messages_guild_id_channels_channel_id_messages_get,
    send_message_guild_id_channels_channel_id_messages_post,
)
from discord_client_service_client.models.channel_info import ChannelInfo
from discord_client_service_client.models.send_message_request import (
    SendMessageRequest,
)
from discord_client_service_client.types import Unset

if TYPE_CHECKING:
    # Standard library
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


@dataclass
class ServiceMessage(Message):
    """Simple Message implementation for service adapter responses."""

    _id: str
    _channel_id: str
    _content: str
    _sender_id: str
    _sender_name: str
    _timestamp: str
    _edited_timestamp: str | None = None

    @property
    def id(self) -> str:
        """Return the unique identifier of the message."""
        return self._id

    @property
    def channel_id(self) -> str:
        """Return the channel ID where the message was sent."""
        return self._channel_id

    @property
    def content(self) -> str:
        """Return the message content."""
        return self._content

    @property
    def sender_id(self) -> str:
        """Return the author's user ID."""
        return self._sender_id

    @property
    def sender_name(self) -> str:
        """Return the author's display name."""
        return self._sender_name

    @property
    def timestamp(self) -> str:
        """Return the timestamp when the message was sent."""
        return self._timestamp

    @property
    def edited_timestamp(self) -> str | None:
        """Return the timestamp when the message was edited, if applicable."""
        return self._edited_timestamp


@dataclass
class ServiceChannel(Channel):
    """Simple Channel implementation for service adapter responses."""

    _id: str
    _name: str
    _channel_type: str

    @property
    def channel_id(self) -> str:
        """Return the unique identifier of the channel."""
        return self._id

    @property
    def name(self) -> str:
        """Return the channel name."""
        return self._name

    @property
    def channel_type(self) -> str:
        """Return the channel type."""
        return self._channel_type


class ServiceAdapterClient(chat_client_api.ChatInterface):
    """Adapter that wraps the auto-generated Discord service client.

    This class implements the chat_client_api.ChatInterface interface by delegating
    to the auto-generated OpenAPI client. It translates between the HTTP/REST
    world and the local interface expected by our application.

    Attributes:
        service_url: Base URL of the Discord service
        guild_id: The guild ID for whom to make requests
        _http_client: The auto-generated HTTP client

    """

    def __init__(
        self, service_url: str = "http://localhost:8000", guild_id: str | None = None
    ) -> None:
        """Initialize the service adapter client.

        Args:
            service_url: Base URL of the running Discord service
            guild_id: The guild ID for making authenticated requests

        """
        self.service_url = service_url
        self.guild_id = guild_id or "default_guild"
        self._http_client = GeneratedClient(base_url=service_url)
        logger.info(
            "Initialized ServiceAdapterClient for guild %s at %s",
            self.guild_id,
            service_url,
        )

    def get_message(self, channel_id: str, message_id: str) -> Message:
        """Get a single message by ID from a channel.

        Args:
            channel_id: The Discord channel ID
            message_id: The message ID to retrieve

        Returns:
            A Message object containing the message details

        Raises:
            ValueError: If the message cannot be retrieved

        """
        try:
            response = get_messages_guild_id_channels_channel_id_messages_get.sync(
                client=self._http_client,
                guild_id=self.guild_id,
                channel_id=channel_id,
                limit=100,
            )
            if response and hasattr(response, "messages") and response.messages:
                for msg in response.messages:
                    if msg.id == message_id:
                        edited_ts = msg.edited_timestamp
                        return ServiceMessage(
                            _id=msg.id,
                            _channel_id=msg.channel_id,
                            _content=msg.content,
                            _sender_id=msg.sender_id,
                            _sender_name=msg.sender_name,
                            _timestamp=msg.timestamp,
                            _edited_timestamp=None if isinstance(edited_ts, Unset) else edited_ts,
                        )
            error_msg = f"Message {message_id} not found in channel {channel_id}"
            raise ValueError(error_msg)
        except ValueError:
            raise
        except Exception as e:
            logger.exception("Failed to get message %s from channel %s", message_id, channel_id)
            error_msg = f"Failed to get message: {e}"
            raise ValueError(error_msg) from e

    def get_messages(self, channel_id: str, limit: int = 10) -> list[Message]:
        """Get messages from a Discord channel.

        Args:
            channel_id: The Discord channel ID
            limit: Maximum number of messages to return

        Yields:
            Message objects

        """
        results: list[Message] = []
        try:
            response = get_messages_guild_id_channels_channel_id_messages_get.sync(
                client=self._http_client,
                guild_id=self.guild_id,
                channel_id=channel_id,
                limit=limit,
            )
            if response and hasattr(response, "messages") and response.messages:
                for msg in response.messages:
                    edited_ts = msg.edited_timestamp
                    results.append(
                        ServiceMessage(
                            _id=msg.id,
                            _channel_id=msg.channel_id,
                            _content=msg.content,
                            _sender_id=msg.sender_id,
                            _sender_name=msg.sender_name,
                            _timestamp=msg.timestamp,
                            _edited_timestamp=None if isinstance(edited_ts, Unset) else edited_ts,
                        )
                    )
        except Exception as e:
            logger.exception("Failed to get messages from channel %s", channel_id)
            error_msg = f"Failed to get messages: {e}"
            raise ValueError(error_msg) from e

        return results

    def send_message(self, channel_id: str, content: str) -> bool:
        """Send a message to a Discord channel.

        Args:
            channel_id: The Discord channel ID
            content: The message content to send

        Returns:
            bool: True if the message was successfully sent, False otherwise

        """
        try:
            request = SendMessageRequest(content=content)
            response = send_message_guild_id_channels_channel_id_messages_post.sync(
                client=self._http_client,
                guild_id=self.guild_id,
                channel_id=channel_id,
                body=request,
            )
            if response and hasattr(response, "status"):
                return bool(response.status == "success")
            return False  # noqa: TRY300
        except Exception as e:
            logger.exception("Failed to send message to channel %s", channel_id)
            error_msg = f"Failed to send message: {e}"
            raise ValueError(error_msg) from e

    def delete_message(self, channel_id: str, message_id: str) -> bool:
        """Delete a message from a Discord channel.

        Args:
            channel_id: The Discord channel ID
            message_id: The message ID to delete

        Returns:
            True if the message was successfully deleted, False otherwise

        """
        try:
            response = delete_message_guild_id_channels_channel_id_messages_message_id_delete.sync(
                client=self._http_client,
                guild_id=self.guild_id,
                channel_id=channel_id,
                message_id=message_id,
            )
            if response and hasattr(response, "status"):
                return bool(response.status == "success")
            return False  # noqa: TRY300
        except Exception:
            logger.exception("Failed to delete message %s from channel %s", message_id, channel_id)
            return False

    def get_channel(self, channel_id: str) -> Channel:
        """Get information about a specific Discord channel.

        Args:
            channel_id: The Discord channel ID

        Returns:
            A Channel object containing channel details

        Raises:
            ValueError: If the channel cannot be retrieved

        """
        try:
            response = get_channel_guild_id_channels_channel_id_get.sync(
                client=self._http_client,
                guild_id=self.guild_id,
                channel_id=channel_id,
            )
            if isinstance(response, ChannelInfo):
                # Use 'type_' attribute if 'type' doesn't exist
                channel_type = getattr(response, "type", None) or getattr(
                    response, "type_", "unknown"
                )
                return ServiceChannel(
                    _id=response.id,
                    _name=response.name,
                    _channel_type=str(channel_type),
                )
            error_msg = f"Channel {channel_id} not found"
            raise ValueError(error_msg)
        except ValueError:
            raise
        except Exception as e:
            logger.exception("Failed to get channel %s", channel_id)
            error_msg = f"Failed to get channel: {e}"
            raise ValueError(error_msg) from e

    def get_channels(self) -> Iterator[Channel]:
        """Get all accessible Discord channels for the user.

        Yields:
            Channel objects

        """
        try:
            response = get_channels_guilds_guild_id_channels_get.sync(
                client=self._http_client,
                guild_id=self.guild_id,
            )
            if response and hasattr(response, "channels") and response.channels:
                for ch in response.channels:
                    # Use 'type_' attribute if 'type' doesn't exist
                    channel_type = getattr(ch, "type", None) or getattr(ch, "type_", "unknown")
                    yield ServiceChannel(
                        _id=ch.id,
                        _name=ch.name,
                        _channel_type=str(channel_type),
                    )
        except Exception as e:
            logger.exception("Failed to get channels")
            error_msg = f"Failed to get channels: {e}"
            raise ValueError(error_msg) from e
