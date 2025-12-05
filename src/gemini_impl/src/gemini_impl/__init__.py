"""Gemini implementation for the shared AIService interface."""

from .message import register as register_message
from .tool_call import register as register_tool_call
from .client import register as register_client


def register() -> None:
    """Register all Gemini implementations with ai_client_api."""
    register_message()
    register_tool_call()
    register_client()
