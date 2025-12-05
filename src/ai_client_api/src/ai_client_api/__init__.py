"""Abstract API for AI Chat Service.

This package defines the contract for what an AI chat service should do,
independent of implementation details or specific AI providers.
"""

from ai_client_api.client import AIService as AIService
from ai_client_api.client import Message as Message
from ai_client_api.client import ToolCall as ToolCall
from ai_client_api.client import get_client as get_client
from ai_client_api.client import get_message as get_message
from ai_client_api.client import get_tool_call as get_tool_call
from ai_client_api.credential import AICredentialManager as AICredentialManager
from ai_client_api.credential import resolve_api_key as resolve_api_key
