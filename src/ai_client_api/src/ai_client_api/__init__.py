"""Abstract API for AI Chat Service.

This package defines the contract for what an AI chat service should do,
independent of implementation details or specific AI providers.
"""

from ai_client_api.client import AIClient as AIClient
from ai_client_api.client import Message as Message
from ai_client_api.client import get_client as get_client
from ai_client_api.client import get_message as get_message
