import logging
import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from gemini_api import AIClient, Message
from gemini_impl.client import GeminiClient
from gemini_impl.oauth import OAuthManager
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class SendMessageRequest(BaseModel):
    user_id: str
    message: str


class SendMessageResponse(BaseModel):
    response: str


class ConversationHistoryResponse(BaseModel):
    user_id: str
    messages: list[Message]


class ClearConversationResponse(BaseModel):
    user_id: str
    success: bool


class AuthUrlResponse(BaseModel):
    auth_url: str


class AuthCallbackRequest(BaseModel):
    user_id: str
    code: str


class AuthCallbackResponse(BaseModel):
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
    """Dependency that provides an OAuth manager instance."""
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    db_path = os.getenv("GEMINI_DB_PATH", "conversations.db")

    if not Path(credentials_file).exists():
        msg = "OAuth credentials file not configured"
        raise HTTPException(
            status_code=500,
            detail=msg,
        )

    return OAuthManager(credentials_file=credentials_file, db_path=db_path)


_mock_client_instance: AIClient | None = None


def _get_mock_client() -> AIClient:
    """Create a mock AI client for testing.

    Returns a singleton instance to maintain state across requests.
    """
    global _mock_client_instance  # noqa: PLW0603

    if _mock_client_instance is not None:
        return _mock_client_instance

    class MockClient:
        def __init__(self) -> None:
            self.conversations: dict[str, list[Message]] = {}

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

            self.conversations[user_id].append(Message(role="user", content=message))
            self.conversations[user_id].append(Message(role="assistant", content=response))

            return response

        def get_conversation_history(self, user_id: str) -> list[Message]:
            if not user_id:
                msg = "user_id cannot be empty"
                raise ValueError(msg)
            return self.conversations.get(user_id, [])

        def clear_conversation(self, user_id: str) -> bool:
            if not user_id:
                msg = "user_id cannot be empty"
                raise ValueError(msg)
            if user_id in self.conversations:
                del self.conversations[user_id]
                return True
            return False

    _mock_client_instance = MockClient()  # type: ignore[assignment]
    return _mock_client_instance  # type: ignore[return-value]


def _reset_mock_client() -> None:
    """Reset the mock client instance (for testing)."""
    global _mock_client_instance  # noqa: PLW0603
    _mock_client_instance = None


ClientDep = Annotated[AIClient, Depends(get_ai_client)]


def _get_oauth_dep() -> OAuthManager:
    """OAuth dependency wrapper."""
    return get_oauth_manager()


OAuthDep = Annotated[OAuthManager, Depends(_get_oauth_dep)]


@router.post("/chat", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest, client: ClientDep) -> SendMessageResponse:
    """Send a message to the AI and get a response."""
    try:
        response = client.send_message(request.user_id, request.message)
        return SendMessageResponse(response=response)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error sending message")
        raise HTTPException(status_code=500, detail=f"Error sending message: {e!s}") from e


@router.get("/history/{user_id}", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    user_id: str,
    client: ClientDep,
) -> ConversationHistoryResponse:
    """Retrieve conversation history for a user."""
    try:
        messages = client.get_conversation_history(user_id)
        return ConversationHistoryResponse(user_id=user_id, messages=messages)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error fetching conversation history")
        raise HTTPException(status_code=500, detail=f"Error fetching history: {e!s}") from e


@router.delete("/history/{user_id}", response_model=ClearConversationResponse)
async def clear_conversation(
    user_id: str,
    client: ClientDep,
) -> ClearConversationResponse:
    """Clear conversation history for a user."""
    try:
        success = client.clear_conversation(user_id)
        return ClearConversationResponse(user_id=user_id, success=success)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error clearing conversation")
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {e!s}") from e


@router.get("/auth/login", response_model=AuthUrlResponse)
async def get_auth_url(
    oauth_manager: OAuthDep,
    user_id: str = Query(..., description="Unique user identifier"),
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


@router.get("/auth/callback", response_model=AuthCallbackResponse)
async def handle_auth_callback(
    oauth_manager: OAuthDep,
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State parameter from Google"),
) -> AuthCallbackResponse:
    """Handle OAuth callback and store user credentials.

    This endpoint receives the authorization code and state from Google's OAuth redirect.
    The user_id is extracted from the state parameter or stored session.
    """
    try:
        # For now, we'll use a default user_id since the code is user-specific
        # In a real app, you'd store the user_id in the state parameter
        user_id = "authenticated_user"
        oauth_manager.handle_callback(user_id, code)
        return AuthCallbackResponse(user_id=user_id, status="authenticated")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error handling auth callback")
        raise HTTPException(status_code=500, detail=f"Error during authentication: {e!s}") from e


def _raise_not_found() -> None:
    """Raise not found exception for credentials."""
    msg = "No credentials found for user"
    raise HTTPException(status_code=404, detail=msg)


@router.delete("/auth/{user_id}")
async def revoke_auth(
    user_id: str,
    oauth_manager: OAuthDep,
) -> dict[str, str]:
    """Revoke OAuth credentials for a user."""
    try:
        success = oauth_manager.revoke_credentials(user_id)
        if not success:
            _raise_not_found()
        return {"user_id": user_id, "status": "revoked"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error revoking credentials")
        raise HTTPException(status_code=500, detail=f"Error revoking credentials: {e!s}") from e
