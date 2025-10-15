import logging

from fastapi import APIRouter, HTTPException

import gmail_client_impl  # noqa: F401
from mail_client_api import get_client

logger = logging.getLogger(__name__)

router = APIRouter()

try:
    mail_client = get_client(interactive=False)
except RuntimeError as e:
    if "No valid credentials found" in str(e):

        class MockMessage:
            def __init__(self, id: str, subject: str, from_: str, body: str) -> None:
                self.id = id
                self.subject = subject
                self.from_ = from_
                self.body = body

        class MockClient:
            def __init__(self) -> None:
                self.messages = [
                    MockMessage("1", "Test Email 1", "test1@example.com", "This is test message 1"),
                    MockMessage("2", "Test Email 2", "test2@example.com", "This is test message 2"),
                    MockMessage("3", "Test Email 3", "test3@example.com", "This is test message 3"),
                ]

            def get_messages(self, max_results: int = 10) -> list[MockMessage]:
                return self.messages[:max_results]

            def get_message(self, message_id: str) -> MockMessage:
                for msg in self.messages:
                    if msg.id == message_id:
                        return msg
                error_msg = f"Message {message_id} not found"
                raise KeyError(error_msg)

            def delete_message(self, message_id: str) -> bool:
                for i, msg in enumerate(self.messages):
                    if msg.id == message_id:
                        del self.messages[i]
                        return True
                return False

            def mark_as_read(self, message_id: str) -> bool:
                return True

        mail_client = MockClient()  # type: ignore[assignment]
    else:
        raise


@router.get("/messages")
async def get_messages() -> dict[str, list[dict[str, str]]]:
    try:
        messages_iter = mail_client.get_messages()

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
    except Exception as e:
        logger.exception("Error fetching messages: %s", e)
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {e!s}")


@router.get("/messages/{message_id}")
async def get_message(message_id: str) -> dict[str, dict[str, str]]:
    try:
        message = mail_client.get_message(message_id)
        return {
            "message": {
                "id": message.id,
                "subject": message.subject,
                "sender": message.from_,
                "body": message.body,
            },
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Message not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/messages/{message_id}")
async def delete_message(message_id: str) -> dict[str, str]:
    try:
        success = mail_client.delete_message(message_id)
        if success:
            return {"message_id": message_id, "status": "Deleted"}
        raise HTTPException(status_code=500, detail="Failed to delete message")
    except KeyError:
        raise HTTPException(status_code=404, detail="Message not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/messages/{message_id}/mark-as-read")
async def mark_message_as_read(message_id: str) -> dict[str, str]:
    try:
        success = mail_client.mark_as_read(message_id)
        if success:
            return {"message_id": message_id, "status": "Marked as read"}
        raise HTTPException(status_code=500, detail="Failed to mark message as read")
    except KeyError:
        raise HTTPException(status_code=404, detail="Message not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
