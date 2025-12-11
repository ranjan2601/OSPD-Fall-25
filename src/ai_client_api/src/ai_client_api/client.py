"""Abstract interface for AI service clients aligned with OSS-APIs standard.

This module defines the contract that all AI service implementations must follow,
independent of the underlying AI provider (e.g., Gemini, OpenAI).

Implements structured output pattern: AI returns either conversational strings
or structured data matching a provided JSON schema.
"""

from abc import ABC, abstractmethod
from typing import Any


class AIInterface(ABC):
    """Abstract base class for AI service implementations.

    Defines the contract for interacting with an AI service,
    supporting both conversational and structured output modes.
    """

    @abstractmethod
    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate a response from the AI.

        Args:
            user_input: The text provided by the user.
            system_prompt: The instruction set (e.g., "You are a helpful assistant...").
            response_schema: An optional JSON schema (dict).
                If provided, the AI must return a structured Dict matching this schema.
                If None, the AI returns a conversational String.

        Returns:
            A string (conversational response) or a Dict (structured output).

        Raises:
            ValueError: If user_input or system_prompt is empty.
            RuntimeError: If there's an error communicating with the AI service.

        """


def get_client(api_key: str) -> AIInterface:
    """Return an instance of an AI service.

    Args:
        api_key: API key for the AI service.

    Returns:
        AIInterface: An instance conforming to the AIInterface contract.

    Raises:
        NotImplementedError: If the function is not overridden by an implementation.

    """
    raise NotImplementedError
