"""Google Gemini API implementation of AIInterface aligned with OSS-APIs standard."""

from typing import Any

import ai_client_api
import google.generativeai as genai
from ai_client_api.client import AIInterface


class GeminiClient(AIInterface):
    """Gemini implementation following the shared AIInterface contract.

    Supports both conversational responses and structured output via JSON schema.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("api_key cannot be empty")

        self.api_key = api_key

        # Initialize Gemini API
        genai.configure(api_key=api_key)
        self.model: Any = genai.GenerativeModel("gemini-2.0-flash")

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate a response from Gemini using structured output when needed.

        Args:
            user_input: The user's message/input text.
            system_prompt: System instruction for the model.
            response_schema: Optional JSON schema dict for structured output.
                If provided, Gemini will return a dict matching this schema.
                If None, returns a conversational string.

        Returns:
            A string (conversational) or dict (structured output).

        Raises:
            ValueError: If user_input or system_prompt is empty.
            RuntimeError: If there's an error calling the Gemini API.
        """
        if not user_input:
            raise ValueError("user_input cannot be empty")
        if not system_prompt:
            raise ValueError("system_prompt cannot be empty")

        try:
            if response_schema:
                # Structured output mode: configure schema and parse as JSON
                response = self.model.generate_content(
                    [system_prompt, user_input],
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                    ),
                )
                # Parse JSON response
                import json

                return json.loads(response.text)
            else:
                # Conversational mode: return plain text response
                response = self.model.generate_content([system_prompt, user_input])
                return response.text or ""
        except Exception as e:
            raise RuntimeError(f"Error calling Gemini API: {e}") from e


def get_client_impl(api_key: str) -> ai_client_api.AIInterface:
    """Factory for creating a GeminiClient instance."""
    return GeminiClient(api_key=api_key)


def register() -> None:
    """Register this Gemini implementation with ai_client_api."""
    ai_client_api.get_client = get_client_impl
