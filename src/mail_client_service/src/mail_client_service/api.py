"""FastAPI routes for mail client service with mock and real Gmail integration.

This module defines all API endpoints for the mail client service,
providing message retrieval, deletion, and read status management.
"""

import logging
from typing import Annotated

import gmail_client_impl  # noqa: F401
import mail_client_api
from fastapi import APIRouter, Depends, HTTPException
from mail_client_api import Client

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency function that provides the mail client
def get_mail_client() -> Client:
    """Dependency that provides a mail client instance.

    This function attempts to get a real Gmail client, but falls back to a mock
    client if credentials are not available (useful for testing and CI environments).
    """
    try:
        return mail_client_api.get_client(interactive=False)
    except RuntimeError as e:
        if "No valid credentials found" in str(e):
            # Return a mock client for testing/CI environments
            logger.warning("No valid credentials found, using MockClient")
            return _get_mock_client()
        raise


def _get_mock_client() -> Client:  # noqa: C901
    """Create a mock client for testing purposes."""

    class MockMessage:
        """Mock message object for testing."""

        def __init__(self, msg_id: str, subject: str, from_: str, body: str) -> None:
            """Initialize a mock message.

            Args:
                msg_id: Message ID.
                subject: Message subject.
                from_: Message sender.
                body: Message body.

            """
            self.id = msg_id
            self.subject = subject
            self.from_ = from_
            self.body = body

    class MockClient:
        """Mock mail client for testing."""

        def __init__(self) -> None:
            """Initialize with sample messages."""
            self.messages = [
                MockMessage("1", "Test Email 1", "test1@example.com", "This is test message 1"),
                MockMessage("2", "Test Email 2", "test2@example.com", "This is test message 2"),
                MockMessage("3", "Test Email 3", "test3@example.com", "This is test message 3"),
            ]

        def get_messages(self, max_results: int = 10) -> list[MockMessage]:
            """Get messages up to max_results."""
            return self.messages[:max_results]

        def get_message(self, message_id: str) -> MockMessage:
            """Get a single message by ID."""
            for msg in self.messages:
                if msg.id == message_id:
                    return msg
            error_msg = f"Message {message_id} not found"
            raise KeyError(error_msg)

        def delete_message(self, message_id: str) -> bool:
            """Delete a message by ID."""
            for i, msg in enumerate(self.messages):
                if msg.id == message_id:
                    del self.messages[i]
                    return True
            return False

        def mark_as_read(self, _message_id: str) -> bool:
            """Mark a message as read."""
            return True

    return MockClient()


# Type alias for dependency injection (must be after get_mail_client definition)
ClientDep = Annotated[Client, Depends(get_mail_client)]


@router.get("/messages")
async def get_messages(client: ClientDep) -> dict[str, list[dict[str, str]]]:
    """Fetch a list of messages from the inbox."""
    try:
        messages_iter = client.get_messages()
        messages = list(messages_iter)

        return {
            "messages": [
                {
                    "id": msg.id,
                    "subject": msg.subject,
                    "sender": msg.from_,
                    "body": msg.body,
                }
                for msg in messages
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching messages")
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {e!s}") from e


@router.get("/messages/{message_id}")
async def get_message(message_id: str, client: ClientDep) -> dict[str, dict[str, str]]:
    """Fetch a single message by ID."""
    try:
        message = client.get_message(message_id)
        return {
            "message": {
                "id": message.id,
                "subject": message.subject,
                "sender": message.from_,
                "body": message.body,
            },
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Message not found") from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/messages/{message_id}")
async def delete_message(message_id: str, client: ClientDep) -> dict[str, str]:
    """Delete a message by ID."""
    try:
        success = client.delete_message(message_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Message not found") from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if success:
        return {"message_id": message_id, "status": "Deleted"}
    msg = "Failed to delete message"
    raise HTTPException(status_code=500, detail=msg)


@router.post("/messages/{message_id}/mark-as-read")
async def mark_message_as_read(message_id: str, client: ClientDep) -> dict[str, str]:
    """Mark a message as read by ID."""
    try:
        success = client.mark_as_read(message_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Message not found") from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if success:
        return {"message_id": message_id, "status": "Marked as read"}
    msg = "Failed to mark message as read"
    raise HTTPException(status_code=500, detail=msg)
