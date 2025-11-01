"""Adapter connecting abstract Gemini API to FastAPI service via HTTP client.

This package provides an adapter that implements the AIClient interface
while delegating HTTP calls to the auto-generated Gemini service client.
"""

from ._impl import GeminiServiceAdapter

__all__ = ["GeminiServiceAdapter"]
