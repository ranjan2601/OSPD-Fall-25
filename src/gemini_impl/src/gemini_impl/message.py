"""Concrete implementation of Message for Gemini."""

from dataclasses import dataclass

import ai_client_api
from ai_client_api.client import Message


@dataclass
class MessageImpl(Message):
    """Concrete implementation of the Message ABC."""

    _role: str
    _content: str

    def __init__(self, role: str, content: str) -> None:
        """Initialize a message with role and content."""
        self._role = role
        self._content = content

    @property
    def role(self) -> str:
        """Return the message role."""
        return self._role

    @property
    def content(self) -> str:
        """Return the message content."""
        return self._content


def get_message_impl(role: str, content: str) -> ai_client_api.Message:
    """Return an instance of the concrete MessageImpl implementation.

    Args:
        role: The role of the message sender ("user" or "assistant").
        content: The text content of the message.

    Returns:
        Message: A MessageImpl instance.

    """
    return MessageImpl(role=role, content=content)


def register() -> None:
    """Register the Gemini message implementation with the AI client API."""
    ai_client_api.get_message = get_message_impl
