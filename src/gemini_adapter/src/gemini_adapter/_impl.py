"""Adapter implementation connecting abstract API to Gemini FastAPI service."""

from gemini_api import AIClient, Message
from gemini_service_api_client.gemini_ai_service_client import Client as GeminiHTTPClient


class GeminiServiceAdapter(AIClient):
    """Adapter that connects the abstract Gemini API to the FastAPI service via HTTP.

    This adapter implements the AIClient interface while delegating all calls
    to the auto-generated Gemini service HTTP client.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        """Initialize the adapter.

        Args:
            base_url: Base URL of the Gemini FastAPI service.
                     Defaults to localhost:8000.

        """
        self.client = GeminiHTTPClient(base_url=base_url)

    def send_message(self, user_id: str, message: str) -> str:
        """Send a message via the Gemini FastAPI service.

        Args:
            user_id: Unique identifier for the user.
            message: The message text to send.

        Returns:
            The AI's response as a string.

        Raises:
            ValueError: If user_id or message is empty.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        if not message:
            msg = "message cannot be empty"
            raise ValueError(msg)

        response = self.client.send_message_chat_post(
            json_body={"user_id": user_id, "message": message},
        )
        return response.response

    def get_conversation_history(self, user_id: str) -> list[Message]:
        """Retrieve conversation history via the Gemini FastAPI service.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            A list of Message objects representing the conversation history.

        Raises:
            ValueError: If user_id is empty.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)

        response = self.client.get_conversation_history_history_user_id_get(
            user_id=user_id,
        )
        if hasattr(response, "messages") and response.messages:
            return [
                Message(
                    role=msg.role,
                    content=msg.content,
                )
                for msg in response.messages
            ]
        return []

    def clear_conversation(self, user_id: str) -> bool:
        """Clear conversation history via the Gemini FastAPI service.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            True if the conversation was successfully cleared.

        Raises:
            ValueError: If user_id is empty.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)

        response = self.client.clear_conversation_history_user_id_delete(
            user_id=user_id,
        )
        return response.cleared if hasattr(response, "cleared") else True
