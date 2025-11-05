"""Concrete implementation of Message for Gemini."""

from dataclasses import dataclass

from gemini_api.client import Message


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
