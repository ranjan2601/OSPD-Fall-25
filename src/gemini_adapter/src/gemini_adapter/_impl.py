"""Adapter implementation connecting abstract API to Gemini FastAPI service."""

from typing import Any, List, Optional

from ai_client_api.client import AIService, ToolCall
from gemini_service_api_client.gemini_ai_service_client import Client as GeminiHTTPClient


class GeminiServiceAdapter(AIService):
    """Adapter that connects the abstract API to the FastAPI service via HTTP.

    This adapter implements the AIService interface while delegating all calls
    to the auto-generated Gemini service HTTP client.
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        """Initialize the adapter.

        Args:
            base_url: Base URL of the Gemini FastAPI service.

        """
        self.client = GeminiHTTPClient(base_url=base_url)

    def send_message(
        self,
        user_id: str,
        prompt: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """Send a message via the Gemini FastAPI service.

        Args:
            user_id: Unique identifier for the user.
            prompt: The user's message/prompt text.
            context: Optional context containing tools, etc.

        Returns:
            The AI's response as a string.

        Raises:
            ValueError: If user_id or prompt is empty.

        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
        if not prompt:
            raise ValueError("prompt cannot be empty")

        request_data: dict[str, Any] = {
            "user_id": user_id,
            "prompt": prompt,
        }

        if context and "tools" in context:
            request_data["tools"] = context["tools"]

        response = self.client.send_message_send_message_post(
            json_body=request_data,
        )
        return response.text

    def extract_tool_calls(self, response: str) -> List[ToolCall]:
        """Extract tool calls from response.

        Args:
            response: The text response from send_message.

        Returns:
            List of ToolCall objects. Empty list if no tools were called.

        """
        return []
