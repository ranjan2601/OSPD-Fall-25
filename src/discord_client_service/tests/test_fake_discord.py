"""Fake Discord client implementations for testing the Discord service API.

These mimic the minimal behavior the API expects from the real clients so
the HTTP routes can be tested deterministically.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Imported only for type checking to avoid runtime dependency warnings
    from collections.abc import Iterable

from chat_client_api.exceptions import MessageNotFoundError


class FakeChannel:
    """A fake channel used in tests."""

    def __init__(self, id_: str, name: str, channel_type: str = "text") -> None:
        """Create a FakeChannel.

        Args:
            id_: Channel identifier.
            name: Channel name.
            channel_type: Type of the channel (default: "text").

        """
        self.channel_id = id_
        self.name = name
        self.channel_type = channel_type


class FakeMessage:
    """A minimal fake message representation for tests."""

    def __init__(  # noqa: PLR0913 - simple data holder used in tests
        self,
        id_: str,
        channel_id: str,
        sender_id: str = "user1",
        sender_name: str = "Alice",
        content: str = "hello",
        timestamp: str = "2025-10-01T12:00:00Z",
        edited_timestamp: str | None = None,
    ) -> None:
        """Initialize a FakeMessage.

        Args:
            id_: Message id.
            channel_id: Channel the message belongs to.
            sender_id: Sender identifier.
            sender_name: Sender display name.
            content: Message content.
            timestamp: ISO timestamp string.
            edited_timestamp: ISO timestamp string or None.

        """
        self.id = id_
        self.channel_id = channel_id
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.content = content
        self.timestamp = timestamp
        self.edited_timestamp = edited_timestamp


class FakeBotClient:
    """A minimal bot client used for guild-level operations."""

    def __init__(self, channels: Iterable[FakeChannel] | None = None) -> None:
        """Create a FakeBotClient.

        Args:
            channels: Optional iterable of channels to expose for the guild.

        """
        self._channels = list(channels or [])

    def get_guild_channels(self, _guild_id: str) -> Iterable[FakeChannel]:
        """Return the configured guild channels. The guild id is ignored in tests."""
        return self._channels

    def leave_guild(self, _guild_id: str) -> None:
        """Simulate leaving a guild (no-op for tests)."""
        # no-op for tests
        return


class FakeUserClient:
    """Fake per-user client which supports channel/message operations."""

    def __init__(self) -> None:
        """Initialize in-memory channels and messages used by tests."""
        self._channels = {"c1": FakeChannel("c1", "general")}
        self._messages = {
            "c1": [
                FakeMessage("m1", channel_id="c1", content="first"),
                FakeMessage("m2", channel_id="c1", content="second"),
            ]
        }

    def get_channel(self, channel_id: str) -> FakeChannel:
        """Return the channel for the given id or raise ValueError if missing."""
        try:
            return self._channels[channel_id]
        except KeyError as e:
            msg = f"Channel {channel_id} not found"
            raise ValueError(msg) from e

    def get_messages(self, channel_id: str, limit: int = 10) -> list[FakeMessage]:
        """Return up to `max_results` messages for `channel_id`."""
        return self._messages.get(channel_id, [])[:limit]

    def send_message(self, channel_id: str, content: str) -> bool:
        """Create and store a new message in the given channel."""
        if not content:
            err = "message content empty"
            raise ValueError(err)
        msg = FakeMessage("m3", channel_id=channel_id, content=content)
        self._messages.setdefault(channel_id, []).append(msg)
        return True

    def delete_message(self, channel_id: str, message_id: str) -> None:
        """Delete a message by id from a channel or raise MessageNotFoundError."""
        msgs = self._messages.get(channel_id, [])
        for i, m in enumerate(msgs):
            if m.id == message_id:
                del msgs[i]
                return
        # Simulate not found
        msg = f"Message {message_id} not found"
        raise MessageNotFoundError(msg)
