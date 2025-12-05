"""Concrete implementation of Message for Gemini."""

from ai_client_api.client import Message
import ai_client_api


class MessageImpl(Message):
    """Concrete implementation of the Message ABC."""

    def __init__(self, text: str) -> None:
        """Initialize a message with text."""
        self._text = text

    @property
    def text(self) -> str:
        """Return the message text."""
        return self._text


def get_message_impl(text: str) -> ai_client_api.Message:
    """Return an instance of the concrete MessageImpl implementation.

    Args:
        text: The message content.

    Returns:
        Message: A MessageImpl instance.
    """
    return MessageImpl(text=text)


def register() -> None:
    """Register the Gemini message implementation with the AI client API."""
    ai_client_api.get_message = get_message_impl
