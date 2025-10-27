"""Abstract API for AI Chat Service.

This package defines the contract for what an AI chat service should do,
independent of implementation details or specific AI providers.
"""

from .client import AIClient, Message

__all__ = ["AIClient", "Message"]
