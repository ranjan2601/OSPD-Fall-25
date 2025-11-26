"""FastAPI routes for Gemini AI chat service with OAuth authentication.

This module defines all API endpoints for the Gemini service, including
chat operations, conversation management, and OAuth authentication flows.
"""

import base64
import binascii
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from ai_client_api.client import AIClient, Message
from gemini_impl.client import GeminiClient
from gemini_impl.message import MessageImpl
from gemini_impl.oauth import OAuthManager
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class SendMessageRequest(BaseModel):
    """Request model for sending a message to the AI.

    Attributes:
        user_id: Unique identifier for the user.
        message: The message text to send.

    """

    user_id: str
    message: str


class SendMessageResponse(BaseModel):
    """Response model for sending a message.

    Attributes:
        response: The AI's response text.

    """

    response: str


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history.

    Attributes:
        user_id: The user whose history is returned.
        messages: List of message objects in the conversation.

    """

    user_id: str
    messages: list[MessageImpl]


class ClearConversationResponse(BaseModel):
    """Response model for clearing conversation.

    Attributes:
        user_id: The user whose conversation was cleared.
        success: Whether the operation succeeded.

    """

    user_id: str
    success: bool


class AuthUrlResponse(BaseModel):
    """Response model for OAuth authentication URL.

    Attributes:
        auth_url: The URL to redirect user to for OAuth authorization.

    """

    auth_url: str


class AuthCallbackRequest(BaseModel):
    """Request model for OAuth callback with API key.

    Attributes:
        user_id: Unique identifier for the user.
        code: Authorization code from Google.
        api_key: Gemini API key provided by user.

    """

    user_id: str
    code: str
    api_key: str


class AuthCallbackResponse(BaseModel):
    """Response model for OAuth callback.

    Attributes:
        user_id: The authenticated user's ID.
        status: Status of the authentication operation.

    """

    user_id: str
    status: str


def get_ai_client() -> AIClient:
    """Dependency that provides an AI client instance.

    Falls back to a mock client if API key is not available.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    db_path = os.getenv("GEMINI_DB_PATH", "conversations.db")

    if not api_key:
        logger.warning("No GEMINI_API_KEY found, using mock client")
        return _get_mock_client()

    return GeminiClient(api_key=api_key, db_path=db_path)


def get_oauth_manager() -> OAuthManager:
    """Dependency that provides an OAuth manager instance.

    Supports two methods of providing credentials:
    1. GOOGLE_CREDENTIALS_B64: Base64-encoded credentials JSON (recommended for production)
    2. GOOGLE_CREDENTIALS_FILE: Path to credentials JSON file (for local development)
    """
    db_path = os.getenv("GEMINI_DB_PATH", "conversations.db")

    # Try base64-encoded credentials first (Fly.io production)
    credentials_b64 = os.getenv("GOOGLE_CREDENTIALS_B64")
    if credentials_b64:
        try:
            credentials_json_str = base64.b64decode(credentials_b64).decode("utf-8")
            credentials_data = json.loads(credentials_json_str)

            # Create a temporary file to store the credentials
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                delete=False,
            ) as temp_file:
                json.dump(credentials_data, temp_file)
                temp_file.flush()
                credentials_file = temp_file.name
                logger.info("Using base64-encoded OAuth credentials from environment")
                return OAuthManager(credentials_file=credentials_file, db_path=db_path)
        except (binascii.Error, json.JSONDecodeError, ValueError) as e:
            logger.exception("Failed to decode GOOGLE_CREDENTIALS_B64")
            msg = "Invalid OAuth credentials in GOOGLE_CREDENTIALS_B64"
            raise HTTPException(status_code=500, detail=msg) from e

    # Fall back to file-based credentials (local development)
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    if not Path(credentials_file).exists():
        msg = "OAuth credentials not configured. Set GOOGLE_CREDENTIALS_B64 or GOOGLE_CREDENTIALS_FILE"
        raise HTTPException(
            status_code=500,
            detail=msg,
        )

    logger.info("Using OAuth credentials from file: %s", credentials_file)
    return OAuthManager(credentials_file=credentials_file, db_path=db_path)


_mock_client_instance: AIClient | None = None

# Per-user API key storage (in-memory)
_user_api_keys: dict[str, str] = {}


class _MockClient(AIClient):
    """Mock AI client for testing."""

    def __init__(self) -> None:
        self.conversations: dict[str, list[MessageImpl]] = {}

    def send_message(self, user_id: str, message: str) -> str:
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        if not message:
            msg = "message cannot be empty"
            raise ValueError(msg)

        response = f"Mock response to: {message}"

        if user_id not in self.conversations:
            self.conversations[user_id] = []

        self.conversations[user_id].append(MessageImpl(role="user", content=message))
        self.conversations[user_id].append(MessageImpl(role="assistant", content=response))

        return response

    def get_conversation_history(self, user_id: str) -> list[Message]:
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        return cast(list[Message], self.conversations.get(user_id, []))

    def clear_conversation(self, user_id: str) -> bool:
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        if user_id in self.conversations:
            del self.conversations[user_id]
            return True
        return False


def _get_mock_client() -> AIClient:
    """Create a mock AI client for testing.

    Returns a singleton instance to maintain state across requests.
    """
    global _mock_client_instance

    if _mock_client_instance is not None:
        return _mock_client_instance

    _mock_client_instance = _MockClient()
    return _mock_client_instance


def _reset_mock_client() -> None:
    """Reset the mock client instance (for testing)."""
    global _mock_client_instance
    _mock_client_instance = None


def _store_user_api_key(user_id: str, api_key: str) -> None:
    """Store API key for a specific user."""
    _user_api_keys[user_id] = api_key


def _get_user_api_key(user_id: str) -> str | None:
    """Retrieve API key for a specific user."""
    return _user_api_keys.get(user_id)


def _raise_unauthorized() -> None:
    """Raise unauthorized exception."""
    msg = "Unauthorized: Cannot access other user's resources"
    raise HTTPException(status_code=403, detail=msg)


def _raise_missing_api_key() -> None:
    """Raise exception for missing API key."""
    msg = "API key not configured for user. Please authenticate and provide API key first."
    raise HTTPException(status_code=400, detail=msg)


def _raise_missing_parameter(param: str) -> None:
    """Raise exception for missing required parameter."""
    msg = f"{param} is required"
    raise HTTPException(status_code=400, detail=msg)


def _verify_user_authorization(authenticated_user_id: str, requested_user_id: str) -> None:
    """Verify that authenticated user can access requested user's resources.

    Args:
        authenticated_user_id: The user who is currently authenticated
        requested_user_id: The user whose resources are being accessed

    Raises:
        HTTPException: If user is not authorized to access the resource

    """
    if authenticated_user_id != requested_user_id:
        _raise_unauthorized()


def _revoke_user_api_key(user_id: str) -> bool:
    """Revoke API key for a user.

    Args:
        user_id: User ID whose API key should be revoked

    Returns:
        True if key was revoked, False if no key existed

    """
    if user_id in _user_api_keys:
        del _user_api_keys[user_id]
        return True
    return False


def _reset_user_api_keys() -> None:
    """Reset all user API keys (for testing)."""
    _user_api_keys.clear()


def _get_client_class() -> type[AIClient]:
    """Get the AI client class to instantiate (configurable via environment)."""
    client_type = os.getenv("AI_CLIENT_TYPE", "gemini")
    if client_type == "gemini":
        return GeminiClient
    msg = f"Unknown AI client type: {client_type}"
    raise ValueError(msg)


def _create_user_client(user_id: str, api_key: str) -> AIClient:
    """Create a client instance for a specific user."""
    client_class = _get_client_class()
    data_dir = os.getenv("GEMINI_DB_PATH", "conversations.db").rsplit("/", 1)[0]
    db_path = f"{data_dir}/conversations_{user_id}.db"
    return client_class(api_key=api_key, db_path=db_path)  # type: ignore[call-arg]


ClientDep = Annotated[AIClient, Depends(get_ai_client)]


def _get_oauth_dep() -> OAuthManager:
    """OAuth dependency wrapper."""
    return get_oauth_manager()


OAuthDep = Annotated[OAuthManager, Depends(_get_oauth_dep)]


@router.post("/chat")
async def send_message(
    request: SendMessageRequest,
    authenticated_user_id: Annotated[str, Query(description="Authenticated user ID from OAuth")],
) -> SendMessageResponse:
    """Send a message to the AI and get a response.

    Args:
        request: The message request with user_id and message
        authenticated_user_id: The user who is currently authenticated (from OAuth)

    Returns:
        SendMessageResponse with AI response

    Raises:
        HTTPException: If user is not authenticated or not authorized

    """
    try:
        # Verify user is accessing their own resources
        _verify_user_authorization(authenticated_user_id, request.user_id)

        # Get user's API key
        api_key = _get_user_api_key(request.user_id)
        if not api_key:
            _raise_missing_api_key()
            return SendMessageResponse(response="")  # Unreachable, but satisfies type checker

        # Create client using factory (allows swapping implementations)
        client = _create_user_client(request.user_id, api_key)

        response = client.send_message(request.user_id, request.message)
        return SendMessageResponse(response=response)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error sending message")
        raise HTTPException(status_code=500, detail=f"Error sending message: {e!s}") from e


@router.get("/history/{user_id}")
async def get_conversation_history(
    user_id: str,
    authenticated_user_id: Annotated[str, Query(description="Authenticated user ID from OAuth")],
) -> ConversationHistoryResponse:
    """Retrieve conversation history for a user.

    Args:
        user_id: The user whose history to retrieve
        authenticated_user_id: The user who is currently authenticated (from OAuth)

    Returns:
        ConversationHistoryResponse with message history

    Raises:
        HTTPException: If user is not authorized to access this history

    """
    try:
        # Verify user is accessing their own history
        _verify_user_authorization(authenticated_user_id, user_id)

        # Get user's API key to create client
        api_key = _get_user_api_key(user_id)
        if not api_key:
            _raise_missing_api_key()
            return ConversationHistoryResponse(user_id=user_id, messages=[])  # Unreachable, but satisfies type checker

        # Create client using factory (allows swapping implementations)
        client = _create_user_client(user_id, api_key)

        messages = client.get_conversation_history(user_id)
        return ConversationHistoryResponse(user_id=user_id, messages=cast(list[MessageImpl], messages))
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error fetching conversation history")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {e!s}") from e


@router.delete("/history/{user_id}")
async def clear_conversation(
    user_id: str,
    authenticated_user_id: Annotated[str, Query(description="Authenticated user ID from OAuth")],
) -> ClearConversationResponse:
    """Clear conversation history for a user.

    Args:
        user_id: The user whose history to clear
        authenticated_user_id: The user who is currently authenticated (from OAuth)

    Returns:
        ClearConversationResponse with success status

    Raises:
        HTTPException: If user is not authorized to clear this history

    """
    try:
        # Verify user is clearing their own history
        _verify_user_authorization(authenticated_user_id, user_id)

        # Get user's API key to create client
        api_key = _get_user_api_key(user_id)
        if not api_key:
            _raise_missing_api_key()
            return ClearConversationResponse(user_id=user_id, success=False)  # Unreachable, but satisfies type checker

        # Create client using factory (allows swapping implementations)
        client = _create_user_client(user_id, api_key)

        success = client.clear_conversation(user_id)
        return ClearConversationResponse(user_id=user_id, success=success)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error clearing conversation")
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {e!s}") from e


@router.get("/auth/login")
async def get_auth_url(
    oauth_manager: OAuthDep,
    user_id: Annotated[str, Query(description="Unique user identifier")],
) -> AuthUrlResponse:
    """Get OAuth authorization URL for user authentication."""
    try:
        auth_url = oauth_manager.get_authorization_url(user_id)
        return AuthUrlResponse(auth_url=auth_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error generating auth URL")
        raise HTTPException(status_code=500, detail=f"Error generating auth URL: {e!s}") from e


@router.get("/auth/callback")
async def handle_auth_callback_get(
    oauth_manager: OAuthDep,
    user_id: Annotated[str, Query(description="User ID from auth/login request")],
    code: Annotated[str, Query(description="Authorization code from Google")],
    _state: Annotated[str | None, Query(description="State parameter from Google")] = None,
) -> dict[str, str]:
    """Handle OAuth callback redirect from Google.

    This is the GET endpoint that Google redirects to after user authentication.
    It processes the authorization code and stores OAuth credentials.
    User must then provide their API key in a separate request.

    Args:
        oauth_manager: OAuth manager dependency
        user_id: User ID from the original auth/login request
        code: Authorization code from Google
        state: State parameter from Google (optional)

    Returns:
        Success message with next steps

    Raises:
        HTTPException: If authentication fails or parameters are invalid

    """
    if not user_id:
        _raise_missing_parameter("user_id")
    if not code:
        _raise_missing_parameter("code")

    try:
        # Handle OAuth callback and store OAuth credentials
        oauth_manager.handle_callback(user_id, code)
        logger.info("User %s OAuth authenticated successfully", user_id)
        return {
            "status": "oauth_authenticated",
            "user_id": user_id,
            "message": "OAuth authentication successful. Now provide your Gemini API key.",
            "next_step": "POST /auth/api-key with your Gemini API key",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error handling auth callback")
        raise HTTPException(status_code=500, detail=f"Error during authentication: {e!s}") from e


@router.post("/auth/callback")
async def handle_auth_callback_post(
    oauth_manager: OAuthDep,
    request: AuthCallbackRequest,
) -> AuthCallbackResponse:
    """Handle OAuth callback with API key (POST endpoint).

    This endpoint receives the authorization code, user_id, and API key from the client.
    The user_id is used to associate the API key with the authenticated user,
    ensuring only that user can use the key.

    Args:
        oauth_manager: OAuth manager dependency
        request: AuthCallbackRequest containing user_id, code, and api_key

    Returns:
        AuthCallbackResponse with user_id and authentication status

    Raises:
        HTTPException: If authentication fails or parameters are invalid

    """
    try:
        user_id = request.user_id
        code = request.code
        api_key = request.api_key

        # Validate inputs
        if not user_id:
            _raise_missing_parameter("user_id")
        if not code:
            _raise_missing_parameter("code")
        if not api_key:
            _raise_missing_parameter("api_key")

        # Handle OAuth callback and store OAuth credentials
        oauth_manager.handle_callback(user_id, code)

        # Store user's API key (isolated per user)
        _store_user_api_key(user_id, api_key)

        logger.info("User %s authenticated successfully with API key stored", user_id)
        return AuthCallbackResponse(user_id=user_id, status="authenticated")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error handling auth callback")
        raise HTTPException(status_code=500, detail=f"Error during authentication: {e!s}") from e


@router.post("/auth/api-key")
async def store_api_key(
    user_id: Annotated[str, Query(description="User ID")],
    api_key: Annotated[str, Query(description="Gemini API key")],
) -> dict[str, str]:
    """Store API key for an authenticated user.

    After OAuth authentication, user provides their Gemini API key.
    This key is stored per-user and required to use the chat service.

    Args:
        user_id: The authenticated user ID
        api_key: The Gemini API key to store

    Returns:
        Success message

    Raises:
        HTTPException: If parameters are invalid

    """
    if not user_id:
        _raise_missing_parameter("user_id")
    if not api_key:
        _raise_missing_parameter("api_key")

    try:
        # Store user's API key (isolated per user)
        _store_user_api_key(user_id, api_key)

        logger.info("API key stored for user %s", user_id)
        return {
            "status": "api_key_stored",
            "user_id": user_id,
            "message": "API key stored successfully. You can now use the chat service.",
        }
    except Exception as e:
        logger.exception("Error storing API key")
        raise HTTPException(status_code=500, detail=f"Error storing API key: {e!s}") from e


def _raise_not_found() -> None:
    """Raise not found exception for credentials."""
    msg = "No credentials found for user"
    raise HTTPException(status_code=404, detail=msg)


@router.delete("/auth/{user_id}")
async def revoke_auth(
    user_id: str,
    oauth_manager: OAuthDep,
    authenticated_user_id: Annotated[str, Query(description="Authenticated user ID from OAuth")],
) -> dict[str, str]:
    """Revoke OAuth credentials and API key for a user.

    Args:
        user_id: The user whose credentials to revoke
        oauth_manager: OAuth manager dependency
        authenticated_user_id: The user who is currently authenticated (from OAuth)

    Returns:
        Response confirming revocation

    Raises:
        HTTPException: If user is not authorized or credentials don't exist

    """
    try:
        # Verify user is revoking their own credentials
        _verify_user_authorization(authenticated_user_id, user_id)

        # Revoke OAuth credentials
        oauth_success = oauth_manager.revoke_credentials(user_id)

        # Revoke API key
        api_key_success = _revoke_user_api_key(user_id)

        # At least one credential should have been revoked
        if not oauth_success and not api_key_success:
            _raise_not_found()

        logger.info("Revoked credentials for user %s", user_id)
        return {"user_id": user_id, "status": "revoked"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error revoking credentials")
        raise HTTPException(status_code=500, detail=f"Error revoking credentials: {e!s}") from e
