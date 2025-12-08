"""Abstract API for AI Service aligned with OSS-APIs standard.

This package defines the contract for what an AI service should do,
independent of implementation details or specific AI providers.

Supports structured output: AI returns either conversational strings
or structured data matching a provided JSON schema.
"""

from ai_client_api.client import AIInterface as AIInterface
from ai_client_api.client import get_client as get_client
from ai_client_api.credential import AICredentialManager as AICredentialManager
from ai_client_api.credential import resolve_api_key as resolve_api_key
