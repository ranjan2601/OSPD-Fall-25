"""Credential management and API key resolution for AI providers."""

import os
from abc import ABC, abstractmethod
from typing import Optional


class AICredentialManager(ABC):
    """Manages API keys/tokens for different AI providers."""

    @abstractmethod
    def get_api_key(self, user_id: str, provider: str) -> str:
        """Retrieve API key for user and provider.

        Args:
            user_id: The unique identifier for the user.
            provider: The provider name (e.g., 'openai', 'gemini', 'claude').

        Returns:
            The API key for the user and provider.

        Raises:
            ValueError: If no API key is found.

        """
        raise NotImplementedError

    @abstractmethod
    def set_api_key(self, user_id: str, provider: str, api_key: str) -> None:
        """Store API key for user and provider.

        Args:
            user_id: The unique identifier for the user.
            provider: The provider name.
            api_key: The API key to store.

        """
        raise NotImplementedError

    @abstractmethod
    def validate_key(self, provider: str, api_key: str) -> bool:
        """Validate that an API key is valid for the provider.

        Args:
            provider: The provider name.
            api_key: The API key to validate.

        Returns:
            True if the key is valid, False otherwise.

        """
        raise NotImplementedError


def resolve_api_key(
    user_id: str,
    provider: str,
    explicit_key: Optional[str] = None,
    credential_manager: Optional[AICredentialManager] = None,
) -> str:
    """Resolve API key for a user and provider.
    Args:
        user_id: The unique identifier for the user.
        provider: The provider name (e.g., 'openai', 'gemini', 'claude').
        explicit_key: Optional explicit API key to use. Takes highest priority.
        credential_manager: Optional credential manager for session storage lookup.

    Returns:
        The resolved API key.

    Raises:
        ValueError: If no API key can be found through any method.

    """
    if explicit_key:
        return explicit_key.strip()

    provider_key = os.getenv(f"{provider.upper()}_API_KEY")
    if provider_key:
        return provider_key.strip()

    unified_key = os.getenv("AI_API_KEY")
    if unified_key:
        return unified_key.strip()

    if credential_manager:
        try:
            return credential_manager.get_api_key(user_id, provider)
        except ValueError:
            pass

    raise ValueError(
        f"No API key found for {provider} and user {user_id}. "
        "Please provide explicit key, set environment variable, or configure in session."
    )
