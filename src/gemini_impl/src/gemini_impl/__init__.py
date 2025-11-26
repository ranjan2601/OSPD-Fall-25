"""Concrete implementation of AI chat service using Google Gemini API.

This package provides a concrete implementation of the AIClient interface
using Google's Generative AI (Gemini) API with OAuth 2.0 authentication.
"""

from gemini_impl.client import GeminiClient as GeminiClient
from gemini_impl.client import get_client_impl as get_client_impl
from gemini_impl.client import register as _register_client
from gemini_impl.message import MessageImpl as MessageImpl
from gemini_impl.message import get_message_impl as get_message_impl
from gemini_impl.message import register as _register_message
from gemini_impl.oauth import OAuthManager as OAuthManager


def register() -> None:
    """Register the Gemini client and message implementations."""
    _register_client()
    _register_message()


# Dependency Injection happens at import time
register()
