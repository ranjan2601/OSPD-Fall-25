import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

# Add the mail_client_api to Python path
mail_client_api_path = Path(__file__).parent.parent / "mail_client_api/src"
gmail_client_impl_path = Path(__file__).parent.parent / "gmail_client_impl/src"

sys.path.append(str(mail_client_api_path))
sys.path.append(str(gmail_client_impl_path))

import gmail_client_impl
# Now import the factory function
from mail_client_api import get_client

router = APIRouter()

# Initialize the mail client
try:
    mail_client = get_client(interactive=False)
except RuntimeError as e:
    if "No valid credentials found" in str(e):
        # Use mock client for testing when no credentials are available

        class MockMessage:
            def __init__(self, id, subject, from_, body) -> None:
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

            def get_messages(self, max_results=10):
                return self.messages[:max_results]

            def get_message(self, message_id):
                for msg in self.messages:
                    if msg.id == message_id:
                        return msg
                msg = f"Message {message_id} not found"
                raise KeyError(msg)

            def delete_message(self, message_id) -> bool:
                for i, msg in enumerate(self.messages):
                    if msg.id == message_id:
                        del self.messages[i]
                        return True
                return False

            def mark_as_read(self, message_id) -> bool:
                return True  # Mock success

        mail_client = MockClient()
    else:
        raise

@router.get("/messages")
async def get_messages():
    try:
        messages_iter = mail_client.get_messages()

        messages = list(messages_iter)

        return {"messages": [
            {
                "id": msg.id,
                "subject": msg.subject,
                "sender": msg.from_,
                "body": msg.body,
            } for msg in messages
        ]}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {e!s}")

@router.get("/messages/{message_id}")
async def get_message(message_id: str):
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
async def delete_message(message_id: str):
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
async def mark_message_as_read(message_id: str):
    try:
        success = mail_client.mark_as_read(message_id)
        if success:
            return {"message_id": message_id, "status": "Marked as read"}
        raise HTTPException(status_code=500, detail="Failed to mark message as read")
    except KeyError:
        raise HTTPException(status_code=404, detail="Message not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
