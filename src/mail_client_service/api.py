from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path

# Add paths for the implementations
mail_client_api_path = Path(__file__).resolve().parent.parent.parent / "../oss-taapp/src/mail_client_api/src"

sys.path.append(str(mail_client_api_path))

# Don't import Gmail implementations for now - use MockClient
from mail_client_api import get_client

router = APIRouter()

# Initialize the mail client - this will use MockClient since Gmail impl isn't imported
mail_client = get_client()

@router.get("/messages")
async def get_messages():
    try:
        # Convert iterator to list for JSON serialization
        messages = list(mail_client.get_messages())
        return {"messages": [
            {
                "id": msg.id,
                "subject": msg.subject,
                "sender": msg.from_,  # Fixed: use from_ instead of sender
                "body": msg.body
            } for msg in messages
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{message_id}")
async def get_message(message_id: str):
    try:
        message = mail_client.get_message(message_id)
        return {
            "message": {
                "id": message.id,
                "subject": message.subject,
                "sender": message.from_,  # Fixed: use from_ instead of sender
                "body": message.body
            }
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
