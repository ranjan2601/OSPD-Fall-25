"""Adapter connecting abstract AI API to FastAPI service via HTTP client.

This package provides an adapter that implements the AIService interface
while delegating HTTP calls to the auto-generated Gemini service client.
"""

from ._impl import GeminiServiceAdapter as GeminiServiceAdapter
