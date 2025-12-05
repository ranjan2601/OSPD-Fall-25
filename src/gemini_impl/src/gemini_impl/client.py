"""Google Gemini API implementation of AIService (HW3 version)."""

from typing import Any, Dict, Optional, List

import ai_client_api
import google.generativeai as genai
from ai_client_api.client import AIService, ToolCall

from gemini_impl.tool_call import get_tool_call_impl


class GeminiClient(AIService):
    """Gemini implementation following the shared AIService interface."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("api_key cannot be empty")

        self.api_key = api_key

        # Initialize Gemini API
        genai.configure(api_key=api_key)
        self.model: Any = genai.GenerativeModel("gemini-2.0-flash")

    def send_message(
        self,
        user_id: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Send a prompt to Gemini and return the model's response as text.

        Args:
            user_id: Required by interface, but not used for storage in HW3.
            prompt: Text prompt from the user.
            context: Optional dict containing tool definitions, conversation history, etc.

        Returns:
            A plain string response from the Gemini model.
        """

        if not user_id:
            raise ValueError("user_id cannot be empty")
        if not prompt:
            raise ValueError("prompt cannot be empty")

        # Extract tools if provided by Chat service
        tools = None
        if context and "tools" in context:
            tools = context["tools"]

        try:
            # Send prompt to Gemini (tool support added later)
            response = self.model.generate_content(prompt)
            return response.text or ""
        except Exception as e:
            raise RuntimeError(f"Error calling Gemini API: {e}") from e

    def extract_tool_calls(self, response: str) -> List[ToolCall]:
        """Parse Gemini response for tool calls (empty stub for HW3)."""
        # TODO: implement actual Gemini tool call parsing
        return []


def get_client_impl(user_id: str, api_key: str) -> ai_client_api.AIService:
    """Factory for creating a GeminiClient instance."""
    return GeminiClient(api_key=api_key)


def register() -> None:
    """Register this Gemini implementation with ai_client_api."""
    ai_client_api.get_client = get_client_impl
