"""Gemini implementation for the shared AIInterface aligned with OSS-APIs standard."""

from .client import register as register_client


def register() -> None:
    """Register Gemini client implementation with ai_client_api."""
    register_client()
