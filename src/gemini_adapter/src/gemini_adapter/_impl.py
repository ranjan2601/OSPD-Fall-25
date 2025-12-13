"""Adapter implementation connecting AIInterface to Gemini FastAPI service.

This adapter implements the AIInterface contract while delegating all calls
to the auto-generated Gemini service HTTP client.
"""

from typing import Any

from ai_client_api.client import AIInterface
from gemini_ai_service_client import Client as GeminiHTTPClient
from gemini_ai_service_client.models import GenerateResponseRequest


class GeminiServiceAdapter(AIInterface):
    """Adapter that connects the AIInterface to the Gemini FastAPI service via HTTP."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        """Initialize the adapter.

        Args:
            base_url: Base URL of the Gemini FastAPI service.

        """
        self.client = GeminiHTTPClient(base_url=base_url)

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate a response via the Gemini FastAPI service.

        Args:
            user_input: The user's input/prompt text.
            system_prompt: System instruction for the model.
            response_schema: Optional JSON schema for structured output.

        Returns:
            A string (conversational) or dict (structured output).

        Raises:
            ValueError: If user_input or system_prompt is empty.

        """
        if not user_input:
            raise ValueError("user_input cannot be empty")
        if not system_prompt:
            raise ValueError("system_prompt cannot be empty")

        request = GenerateResponseRequest(
            user_input=user_input,
            system_prompt=system_prompt,
            response_schema=response_schema,
        )

        response = self.client.generate_response_generate_post(body=request)
        # Cast from Any to the expected return type
        return str(response.output) if isinstance(response.output, str) else dict(response.output)
