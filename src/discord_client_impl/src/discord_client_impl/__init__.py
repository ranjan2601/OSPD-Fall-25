"""Discord client implementation with OAuth2 authentication.

This module provides a Discord implementation of the chat_client_api contract.
It uses OAuth2 for authentication and the Discord REST API for all operations.

Usage:
    import discord_client_impl  # Side-effect: registers Discord as implementation
    import chat_client_api

    # Get client for a specific user (will use stored credentials)
    client = chat_client_api.get_client(user_id="user123")

    # Or create client directly with access token
    from discord_client_impl import DiscordClient
    client = DiscordClient(access_token="your_token")

"""

import chat_client_api

from discord_client_impl.discord_impl import DiscordClient
from discord_client_impl.message_impl import DiscordChannel, DiscordMessage


def get_client_impl(user_id: str | None = None) -> chat_client_api.ChatInterface:
    """Create a Discord client instance.

    Args:
        user_id: User ID for multi-user authentication (will fetch from database).

    Returns:
        DiscordClient: Configured Discord client instance.

    Note:
        For now, this creates a client without authentication.
        In Phase 4, this will fetch credentials from the database.

    """
    # TODO: In Phase 4, fetch credentials from database using user_id
    # For now, create client with env vars or no token (will need auth flow)
    return DiscordClient()


def get_message_impl(msg_id: str, raw_data: dict[str, str]) -> chat_client_api.Message:
    """Create a Discord message instance.

    Args:
        msg_id: The message ID (unused, kept for interface compatibility).
        raw_data: Raw message data from Discord API.

    Returns:
        DiscordMessage: Discord message instance.

    """
    return DiscordMessage(raw_data)  # type: ignore[arg-type]


def get_channel_impl(channel_id: str, raw_data: dict[str, str]) -> chat_client_api.Channel:
    """Create a Discord channel instance.

    Args:
        channel_id: The channel ID (unused, kept for interface compatibility).
        raw_data: Raw channel data from Discord API.

    Returns:
        DiscordChannel: Discord channel instance.

    """
    return DiscordChannel(raw_data)  # type: ignore[arg-type]


def register() -> None:
    """Register Discord implementations with chat_client_api.

    This function overrides the factory functions in chat_client_api
    to return Discord implementations.

    """
    chat_client_api.get_client = get_client_impl
    chat_client_api.get_message = get_message_impl
    chat_client_api.get_channel = get_channel_impl


# Auto-register on import (side-effect import pattern)
register()
