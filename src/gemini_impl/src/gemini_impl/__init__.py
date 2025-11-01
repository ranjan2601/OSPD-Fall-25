"""Concrete implementation of AI chat service using Google Gemini API.

This package provides a concrete implementation of the AIClient interface
using Google's Generative AI (Gemini) API with OAuth 2.0 authentication.
"""

from .client import GeminiClient
from .oauth import OAuthManager

__all__ = ["GeminiClient", "OAuthManager"]
