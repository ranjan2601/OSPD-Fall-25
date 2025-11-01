"""Abstract interface for AI chat service clients.

This module defines the contract that all AI chat service implementations
must follow, independent of the underlying AI provider (e.g., Gemini, OpenAI).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a single message in a conversation.

    Attributes:
        role: The role of the message sender ("user" or "assistant").
        content: The text content of the message.

    """

    role: str
    content: str


class AIClient(ABC):
    """Abstract base class for AI chat service clients.

    Defines the contract for interacting with an AI chat service,
    independent of the specific provider implementation.
    """

    @abstractmethod
    def send_message(self, user_id: str, message: str) -> str:
        """Send a message and get a response from the AI.

        Args:
            user_id: Unique identifier for the user.
            message: The message text to send.

        Returns:
            The AI's response as a string.

        Raises:
            ValueError: If user_id or message is empty.
            RuntimeError: If there's an error communicating with the AI service.

        """

    @abstractmethod
    def get_conversation_history(self, user_id: str) -> list[Message]:
        """Retrieve the conversation history for a user.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            A list of Message objects representing the conversation history,
            ordered from oldest to newest.

        Raises:
            ValueError: If user_id is empty.

        """

    @abstractmethod
    def clear_conversation(self, user_id: str) -> bool:
        """Clear the conversation history for a user.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            True if the conversation was successfully cleared, False otherwise.

        Raises:
            ValueError: If user_id is empty.

        """
