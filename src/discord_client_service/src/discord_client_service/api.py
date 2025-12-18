"""API endpoints for Discord operations and OAuth2 flow."""

import logging

from chat_client_api.exceptions import MessageDeleteError, MessageNotFoundError
from discord_client_impl.auth_helper import (
    check_user_authenticated,
    delete_user_credentials,
    get_bot_client_for_guild,
    get_client_for_user,
    store_user_credentials,
)
from discord_client_impl.discord_impl import DiscordClient
from fastapi import Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from discord_client_service.service import app

from .auth_session import create_session, create_state, pop_state, require_guild_access

logger = logging.getLogger(__name__)


class OAuthInitResponse(BaseModel):
    """OAuth2 initialization response."""

    authorization_url: str = Field(..., description="URL to redirect user for OAuth")


class MessageDetail(BaseModel):
    """Discord message details."""

    id: str = Field(..., description="Message ID")
    channel_id: str = Field(..., description="Channel ID")
    sender_id: str = Field(..., description="Sender user ID")
    sender_name: str = Field(..., description="Sender display name")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    edited_timestamp: str | None = Field(None, description="Edit timestamp if edited")


class MessageListResponse(BaseModel):
    """List of Discord messages."""

    messages: list[MessageDetail] = Field(..., description="List of messages")
    count: int = Field(..., description="Number of messages returned")


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    content: str = Field(..., min_length=1, max_length=2000, description="Message content")


class ChannelInfo(BaseModel):
    """Discord channel information."""

    id: str = Field(..., description="Channel ID")
    name: str = Field(..., description="Channel name")
    type: str = Field(..., description="Channel type")


class ChannelListResponse(BaseModel):
    """List of Discord channels."""

    channels: list[ChannelInfo] = Field(..., description="List of channels")
    count: int = Field(..., description="Number of channels returned")


class OperationResponse(BaseModel):
    """Generic operation response."""

    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")


@app.get(
    "/auth/login",
    response_model=OAuthInitResponse,
    summary="Initialize OAuth2 flow",
)
def oauth_login() -> OAuthInitResponse:
    """Initialize OAuth2 flow."""
    try:
        client = DiscordClient()

        server_state = create_state(None)

        auth_url, _generated_state = client._get_authorization_url(server_state)

        logger.info("Generated OAuth authorization URL")
        return OAuthInitResponse(authorization_url=auth_url)
    except Exception as e:
        logger.exception("Failed to generate authorization URL")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {e}",
        ) from e


@app.get(
    "/auth/callback",
    summary="Handle OAuth2 callback (GET)",
    include_in_schema=False,
)
async def oauth_callback(
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str | None = Query(None, description="State parameter (may contain guild_id)"),
    guild_id: str | None = Query(None, description="Optional guild_id override"),
) -> RedirectResponse:
    """Handle OAuth2 callback after user authorization.

    This endpoint expects the OAuth provider to redirect here with query params.
    It will exchange the code for tokens, store the credentials associated with
    the guild_id (either provided explicitly or encoded in state), and then
    redirect the browser to /docs.
    """
    try:
        client = DiscordClient()
        token_data = client._exchange_code_for_token(code)

        state_entry = pop_state(state or "")
        gid = guild_id or (state_entry and state_entry.get("guild_id"))
        if not gid:
            msg = (
                "Missing guild_id in callback; ensure state contains guild id "
                "or provide guild_id query param"
            )
            raise ValueError(msg)

        await store_user_credentials(guild_id=gid, token_data=token_data)
        logger.info("Successfully stored credentials for guild: %s", gid)

        session_id = create_session([gid])
        resp = RedirectResponse(url="/docs")
        resp.set_cookie("session_id", session_id, httponly=True, samesite="lax")

    except ValueError as e:
        logger.exception("Token exchange failed during callback")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token exchange failed: {e}",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error during OAuth callback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {e}",
        ) from e
    else:
        return resp


@app.get(
    "/auth/status/{guild_id}",
    response_model=dict[str, bool | str],
    summary="Check authentication status",
)
async def auth_status(
    guild_id: str,
    _auth: None = Depends(require_guild_access),
) -> dict[str, bool | str]:
    """Check if guild is authenticated."""
    authenticated = await check_user_authenticated(guild_id)
    return {"authenticated": authenticated, "guild_id": guild_id}


@app.delete(
    "/auth/logout/{guild_id}",
    response_model=OperationResponse,
    summary="Logout guild",
)
async def oauth_logout(
    guild_id: str,
    _auth: None = Depends(require_guild_access),
) -> OperationResponse:
    """Logout guild by deleting stored credentials."""
    try:
        deleted = await delete_user_credentials(guild_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No credentials found for guild: {guild_id}",
            )

        try:
            bot_client = await get_bot_client_for_guild(guild_id)
        except ValueError:
            logger.debug("No bot client available to leave guild %s; skipping leave", guild_id)
        else:
            try:
                bot_client.leave_guild(guild_id)
                logger.info("Bot left guild %s after logout", guild_id)
            except (AttributeError, RuntimeError) as e:
                logger.warning("Failed to make bot leave guild %s: %s", guild_id, e)

        logger.info("Successfully logged out guild: %s", guild_id)
        return OperationResponse(
            status="success", message=f"Guild {guild_id} logged out successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Logout failed for guild: %s", guild_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {e}",
        ) from e


@app.get(
    "/guilds/{guild_id}/channels",
    response_model=ChannelListResponse,
    summary="Get guild channels",
)
async def get_channels(
    guild_id: str,
    _auth: None = Depends(require_guild_access),
) -> ChannelListResponse:
    """Get list of Discord channels for a guild."""
    try:
        client = await get_bot_client_for_guild(guild_id)
        channels = list(client.get_guild_channels(guild_id))

        channel_list = [
            ChannelInfo(id=channel.channel_id, name=channel.name, type=channel.channel_type)
            for channel in channels
        ]

        logger.info("Retrieved %d channels", len(channel_list))
        return ChannelListResponse(channels=channel_list, count=len(channel_list))

    except ValueError as e:
        logger.warning("Guild %s not authenticated", guild_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not authenticated: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to retrieve channels")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve channels: {e}",
        ) from e


@app.get(
    "/{guild_id}/channels/{channel_id}",
    response_model=ChannelInfo,
    summary="Get channel info",
)
async def get_channel(
    guild_id: str,
    channel_id: str,
    _auth: None = Depends(require_guild_access),
) -> ChannelInfo:
    """Get information about a specific Discord channel."""
    try:
        client = await get_client_for_user(guild_id)
        channel = client.get_channel(channel_id=channel_id)

        logger.info("Retrieved channel %s", channel_id)
        return ChannelInfo(id=channel.channel_id, name=channel.name, type=channel.channel_type)

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {channel_id} not found",
            ) from e
        logger.warning("Guild %s not authenticated", guild_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Guild not authenticated: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to retrieve channel")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve channel: {e}",
        ) from e


@app.get(
    "/{guild_id}/channels/{channel_id}/messages",
    response_model=MessageListResponse,
    summary="Get messages from channel",
)
async def get_messages(
    guild_id: str,
    channel_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of messages"),
    _auth: None = Depends(require_guild_access),
) -> MessageListResponse:
    """Get messages from a Discord channel."""
    try:
        client = await get_client_for_user(guild_id)
        messages = client.get_messages(channel_id=channel_id, limit=limit)

        message_list = [
            MessageDetail(
                id=msg.id,
                channel_id=msg.channel_id,  # type: ignore[attr-defined]
                sender_id=msg.sender_id,
                sender_name=msg.sender_name,  # type: ignore[attr-defined]
                content=msg.content,
                timestamp=msg.timestamp,  # type: ignore[attr-defined]
                edited_timestamp=msg.edited_timestamp,  # type: ignore[attr-defined]
            )
            for msg in messages
        ]

        logger.info("Retrieved %d messages from channel %s", len(message_list), channel_id)
        return MessageListResponse(messages=message_list, count=len(message_list))

    except ValueError as e:
        logger.warning("Guild %s not authenticated: %s", guild_id, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Guild not authenticated: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to retrieve messages")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {e}",
        ) from e


@app.post(
    "/{guild_id}/channels/{channel_id}/messages",
    response_model=OperationResponse,
    summary="Send message to channel",
)
async def send_message(
    guild_id: str,
    channel_id: str,
    request: SendMessageRequest,
    _auth: None = Depends(require_guild_access),
) -> OperationResponse:
    """Send a message to a Discord channel."""
    try:
        client = await get_client_for_user(guild_id)
        try:
            client.send_message(channel_id=channel_id, content=request.content)
        except TypeError:
            client.send_message(channel_id, request.content)

        logger.info("Sent message to channel %s", channel_id)
        return OperationResponse(status="success", message="Message sent")

    except ValueError as e:
        if "not authenticated" in str(e).lower():
            logger.warning("Guild %s not authenticated", guild_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Guild not authenticated: {e}",
            ) from e
        logger.exception("Failed to send message")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send message: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to send message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {e}",
        ) from e


@app.delete(
    "/{guild_id}/channels/{channel_id}/messages/{message_id}",
    response_model=OperationResponse,
    summary="Delete message",
)
async def delete_message(
    guild_id: str,
    channel_id: str,
    message_id: str,
    _auth: None = Depends(require_guild_access),
) -> OperationResponse:
    """Delete a message from a Discord channel."""
    try:
        client = await get_client_for_user(guild_id)
        try:
            client.delete_message(channel_id=channel_id, message_id=message_id)
        except TypeError:
            client.delete_message(channel_id, message_id)

        logger.info("Deleted message %s", message_id)
        return OperationResponse(status="success", message=f"Message {message_id} deleted")

    except MessageNotFoundError as e:
        logger.warning("Message %s not found", message_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except MessageDeleteError as e:
        logger.exception("Failed to delete message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    except ValueError as e:
        logger.warning("Guild %s not authenticated", guild_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not authenticated: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to delete message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {e}",
        ) from e
