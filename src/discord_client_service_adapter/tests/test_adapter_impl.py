"""Unit tests for the Discord ServiceAdapterClient implementation."""

from unittest.mock import MagicMock, patch

import pytest
from discord_client_service_client.models.channel_info import ChannelInfo
from discord_client_service_client.models.channel_list_response import (
    ChannelListResponse,
)
from discord_client_service_client.models.message_detail import MessageDetail
from discord_client_service_client.models.message_list_response import (
    MessageListResponse,
)
from discord_client_service_client.models.operation_response import OperationResponse

from discord_client_service_adapter.adapter_impl import (
    ServiceAdapterClient,
    ServiceChannel,
    ServiceMessage,
)


@pytest.fixture
def adapter() -> ServiceAdapterClient:
    """Fixture for a ServiceAdapterClient instance."""
    return ServiceAdapterClient(service_url="http://testserver", guild_id="test_guild_123")


@patch(
    "discord_client_service_adapter.adapter_impl.get_messages_guild_id_channels_channel_id_messages_get"
)
def test_get_message_success(mock_get_messages: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should retrieve a specific message by ID from a channel."""
    # Mock response with one message
    mock_get_messages.sync.return_value = MessageListResponse(
        messages=[
            MessageDetail(
                id="msg123",
                channel_id="channel456",
                content="Hello, world!",
                sender_id="user789",
                sender_name="TestUser",
                timestamp="2025-01-01T12:00:00Z",
                edited_timestamp=None,
            )
        ],
        count=1,
    )

    message = adapter.get_message(channel_id="channel456", message_id="msg123")

    assert isinstance(message, ServiceMessage)
    assert message.id == "msg123"
    assert message.channel_id == "channel456"
    assert message.content == "Hello, world!"
    assert message.sender_name == "TestUser"
    mock_get_messages.sync.assert_called_once_with(
        client=adapter._http_client,
        guild_id="test_guild_123",
        channel_id="channel456",
        limit=100,
    )


@patch(
    "discord_client_service_adapter.adapter_impl.get_messages_guild_id_channels_channel_id_messages_get"
)
def test_get_message_not_found(mock_get_messages: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should raise ValueError when message is not found."""
    # Mock empty response
    mock_get_messages.sync.return_value = MessageListResponse(messages=[], count=0)

    with pytest.raises(ValueError, match="Message msg999 not found"):
        adapter.get_message(channel_id="channel456", message_id="msg999")


@patch(
    "discord_client_service_adapter.adapter_impl.get_messages_guild_id_channels_channel_id_messages_get"
)
def test_get_messages_success(mock_get_messages: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should retrieve messages from a channel."""
    mock_get_messages.sync.return_value = MessageListResponse(
        messages=[
            MessageDetail(
                id="msg1",
                channel_id="channel456",
                content="First message",
                sender_id="user1",
                sender_name="User One",
                timestamp="2025-01-01T12:00:00Z",
                edited_timestamp=None,
            ),
            MessageDetail(
                id="msg2",
                channel_id="channel456",
                content="Second message",
                sender_id="user2",
                sender_name="User Two",
                timestamp="2025-01-01T12:01:00Z",
                edited_timestamp=None,
            ),
        ],
        count=2,
    )

    messages = list(adapter.get_messages(channel_id="channel456", limit=10))

    assert len(messages) == 2
    assert messages[0].id == "msg1"
    assert messages[0].content == "First message"
    assert messages[1].id == "msg2"
    assert messages[1].content == "Second message"
    mock_get_messages.sync.assert_called_once_with(
        client=adapter._http_client,
        guild_id="test_guild_123",
        channel_id="channel456",
        limit=10,
    )


@patch(
    "discord_client_service_adapter.adapter_impl.send_message_guild_id_channels_channel_id_messages_post"
)
def test_send_message_success(mock_send: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should send a message to a channel."""
    mock_send.sync.return_value = OperationResponse(status="success", message="Message sent")

    result = adapter.send_message(channel_id="channel456", content="Hello from test!")

    assert result is True


@patch(
    "discord_client_service_adapter.adapter_impl.delete_message_guild_id_channels_channel_id_messages_message_id_delete"
)
def test_delete_message_success(mock_delete: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should delete a message successfully."""
    mock_delete.sync.return_value = OperationResponse(status="success", message="Message deleted")

    result = adapter.delete_message(channel_id="channel456", message_id="msg123")

    assert result is True
    mock_delete.sync.assert_called_once_with(
        client=adapter._http_client,
        guild_id="test_guild_123",
        channel_id="channel456",
        message_id="msg123",
    )


@patch(
    "discord_client_service_adapter.adapter_impl.delete_message_guild_id_channels_channel_id_messages_message_id_delete"
)
def test_delete_message_failure(mock_delete: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should return False when delete fails."""
    mock_delete.sync.return_value = OperationResponse(status="failure", message="Error")

    result = adapter.delete_message(channel_id="channel456", message_id="msg123")

    assert result is False


@patch("discord_client_service_adapter.adapter_impl.get_channel_guild_id_channels_channel_id_get")
def test_get_channel_success(mock_get_channel: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should retrieve channel information."""
    mock_get_channel.sync.return_value = ChannelInfo(id="channel456", name="general", type_="text")

    channel = adapter.get_channel(channel_id="channel456")

    assert isinstance(channel, ServiceChannel)
    assert channel.channel_id == "channel456"
    assert channel.name == "general"
    assert channel.channel_type == "text"
    mock_get_channel.sync.assert_called_once_with(
        client=adapter._http_client,
        guild_id="test_guild_123",
        channel_id="channel456",
    )


@patch("discord_client_service_adapter.adapter_impl.get_channels_guilds_guild_id_channels_get")
def test_get_channels_success(mock_get_channels: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should retrieve list of channels."""
    mock_get_channels.sync.return_value = ChannelListResponse(
        channels=[
            ChannelInfo(id="ch1", name="general", type_="text"),
            ChannelInfo(id="ch2", name="announcements", type_="text"),
            ChannelInfo(id="ch3", name="voice-chat", type_="voice"),
        ],
        count=3,
    )

    channels = list(adapter.get_channels())

    assert len(channels) == 3
    assert channels[0].channel_id == "ch1"
    assert channels[0].name == "general"
    assert channels[2].channel_type == "voice"
    mock_get_channels.sync.assert_called_once_with(
        client=adapter._http_client, guild_id="test_guild_123"
    )


@patch(
    "discord_client_service_adapter.adapter_impl.get_messages_guild_id_channels_channel_id_messages_get"
)
def test_get_messages_handles_exception(
    mock_get_messages: MagicMock, adapter: ServiceAdapterClient
) -> None:
    """It should raise ValueError when an exception occurs."""
    mock_get_messages.sync.side_effect = Exception("Network error")

    with pytest.raises(ValueError, match="Failed to get messages"):
        list(adapter.get_messages(channel_id="channel456"))


def test_adapter_initialization() -> None:
    """It should initialize with correct attributes."""
    adapter = ServiceAdapterClient(service_url="http://example.com:8080", guild_id="my_guild")

    assert adapter.service_url == "http://example.com:8080"
    assert adapter.guild_id == "my_guild"
    assert adapter._http_client._base_url == "http://example.com:8080"


def test_adapter_uses_default_guild() -> None:
    """It should use default_guild when guild_id is not provided."""
    adapter = ServiceAdapterClient(service_url="http://example.com")

    assert adapter.guild_id == "default_guild"
