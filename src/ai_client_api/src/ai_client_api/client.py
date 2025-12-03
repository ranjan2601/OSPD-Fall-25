"""Abstract interface for AI chat service clients.

This module defines the contract that all AI chat service implementations
must follow, independent of the underlying AI provider (e.g., Gemini, OpenAI).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Message(ABC):
    """Abstract base class representing a message in a conversation."""

    @property
    @abstractmethod
    def text(self) -> str:
        """Return the message text content."""
        raise NotImplementedError


class ToolCall(ABC):
    """Abstract base class representing a tool/function call made by the AI."""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Name of the tool/function being called."""
        raise NotImplementedError

    @property
    @abstractmethod
    def tool_args(self) -> Dict[str, Any]:
        """Arguments passed to the tool as a dictionary."""
        raise NotImplementedError

    @property
    @abstractmethod
    def tool_id(self) -> str:
        """Unique identifier for this specific tool call invocation."""
        raise NotImplementedError


class AIService(ABC):
    """Abstract base class for AI chat service implementations.

    Defines the contract for interacting with an AI chat service,
    independent of the specific provider implementation.
    """

    @abstractmethod
    def send_message(
        self,
        user_id: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Send a message to the AI model and receive a response.

        Args:
            user_id: Unique identifier for the user.
            prompt: The user's message/prompt text.
            context: Optional dictionary containing:
                - "tools": List of available tool definitions
                - "conversation_history": Previous Message objects
                - Other provider-specific context

        Returns:
            The AI model's response as a plain text string.

        Raises:
            ValueError: If user_id or prompt is empty.
            RuntimeError: If there's an error communicating with the AI service.

        """

    @abstractmethod
    def extract_tool_calls(self, response: str) -> List["ToolCall"]:
        """Extract tool calls from an AI response if present.

        Args:
            response: The text response from send_message.

        Returns:
            List of ToolCall objects. Empty list if no tools were called.

        Raises:
            RuntimeError: If parsing tool calls fails.

        """


def get_client(user_id: str, api_key: str) -> AIService:
    """Return an instance of an AI chat service.

    Args:
        user_id: Unique identifier for the user.
        api_key: API key for the AI service.

    Returns:
        AIService: An instance conforming to the AIService contract.

    Raises:
        NotImplementedError: If the function is not overridden by an implementation.

    """
    raise NotImplementedError


def get_message(text: str) -> Message:
    """Return an instance of a Message.

    Args:
        text: The message text content.

    Returns:
        Message: An instance conforming to the Message contract.

    Raises:
        NotImplementedError: If the function is not overridden by an implementation.

    """
    raise NotImplementedError


def get_tool_call(tool_name: str, tool_args: Dict[str, Any], tool_id: str) -> ToolCall:
    """Return an instance of a ToolCall.

    Args:
        tool_name: Name of the tool being called.
        tool_args: Arguments dictionary for the tool.
        tool_id: Unique identifier for this invocation.

    Returns:
        ToolCall: An instance conforming to the ToolCall contract.

    Raises:
        NotImplementedError: If the function is not overridden by an implementation.

    """
    raise NotImplementedError
