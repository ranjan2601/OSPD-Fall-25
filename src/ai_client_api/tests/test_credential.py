"""Tests for credential management and API key resolution."""

import os
from unittest.mock import patch

import pytest

from ai_client_api.credential import AICredentialManager, resolve_api_key


class ConcreteCredentialManager(AICredentialManager):
    """Concrete implementation of AICredentialManager for testing."""

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.keys: dict[str, dict[str, str]] = {}

    def get_api_key(self, user_id: str, provider: str) -> str:
        """Retrieve API key for user and provider."""
        if user_id not in self.keys or provider not in self.keys[user_id]:
            raise ValueError(f"No key found for {user_id}/{provider}")
        return self.keys[user_id][provider]

    def set_api_key(self, user_id: str, provider: str, api_key: str) -> None:
        """Store API key for user and provider."""
        if user_id not in self.keys:
            self.keys[user_id] = {}
        self.keys[user_id][provider] = api_key

    def validate_key(self, provider: str, api_key: str) -> bool:
        """Validate that an API key is valid for the provider."""
        return len(api_key) > 0


class TestAICredentialManager:
    """Test AICredentialManager ABC."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that AICredentialManager cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AICredentialManager()  # type: ignore[abstract]

    def test_concrete_implementation_works(self) -> None:
        """Test that concrete implementation works."""
        manager = ConcreteCredentialManager()
        manager.set_api_key("user1", "gemini", "key123")
        assert manager.get_api_key("user1", "gemini") == "key123"

    def test_validate_key(self) -> None:
        """Test key validation."""
        manager = ConcreteCredentialManager()
        assert manager.validate_key("gemini", "valid_key") is True
        assert manager.validate_key("gemini", "") is False


class TestResolveApiKey:
    """Test resolve_api_key function."""

    def test_explicit_key_takes_priority(self) -> None:
        """Test that explicit key has highest priority."""
        result = resolve_api_key(
            user_id="user1",
            provider="gemini",
            explicit_key="explicit_key",
        )
        assert result == "explicit_key"

    def test_explicit_key_strips_whitespace(self) -> None:
        """Test that explicit key strips whitespace."""
        result = resolve_api_key(
            user_id="user1",
            provider="gemini",
            explicit_key="  key_with_spaces  ",
        )
        assert result == "key_with_spaces"

    @patch.dict(os.environ, {"GEMINI_API_KEY": "env_gemini_key"})
    def test_provider_specific_env_var(self) -> None:
        """Test provider-specific environment variable."""
        result = resolve_api_key(
            user_id="user1",
            provider="gemini",
        )
        assert result == "env_gemini_key"

    @patch.dict(os.environ, {"OPENAI_API_KEY": "env_openai_key"})
    def test_provider_specific_env_var_different_providers(self) -> None:
        """Test different provider environment variables."""
        result = resolve_api_key(
            user_id="user1",
            provider="openai",
        )
        assert result == "env_openai_key"

    @patch.dict(os.environ, {"AI_API_KEY": "unified_key"}, clear=True)
    def test_unified_env_var(self) -> None:
        """Test unified environment variable."""
        result = resolve_api_key(
            user_id="user1",
            provider="gemini",
        )
        assert result == "unified_key"

    @patch.dict(
        os.environ,
        {"GEMINI_API_KEY": "provider_key", "AI_API_KEY": "unified_key"},
    )
    def test_provider_specific_takes_priority_over_unified(self) -> None:
        """Test that provider-specific env var takes priority over unified."""
        result = resolve_api_key(
            user_id="user1",
            provider="gemini",
        )
        assert result == "provider_key"

    @patch.dict(os.environ, {}, clear=True)
    def test_credential_manager_fallback(self) -> None:
        """Test credential manager as fallback."""
        manager = ConcreteCredentialManager()
        manager.set_api_key("user1", "gemini", "manager_key")

        result = resolve_api_key(
            user_id="user1",
            provider="gemini",
            credential_manager=manager,
        )
        assert result == "manager_key"

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_key_raises_error(self) -> None:
        """Test that missing key raises ValueError."""
        with pytest.raises(
            ValueError,
            match="No API key found for gemini and user user1",
        ):
            resolve_api_key(
                user_id="user1",
                provider="gemini",
            )

    @patch.dict(os.environ, {}, clear=True)
    def test_manager_missing_key_raises_error(self) -> None:
        """Test that manager with missing key raises ValueError."""
        manager = ConcreteCredentialManager()

        with pytest.raises(
            ValueError,
            match="No API key found for gemini and user user1",
        ):
            resolve_api_key(
                user_id="user1",
                provider="gemini",
                credential_manager=manager,
            )

    @patch.dict(os.environ, {}, clear=True)
    def test_priority_order_all_methods(self) -> None:
        """Test complete priority order with all methods available."""
        manager = ConcreteCredentialManager()
        manager.set_api_key("user1", "gemini", "manager_key")

        # Only manager key available
        result = resolve_api_key(
            user_id="user1",
            provider="gemini",
            credential_manager=manager,
        )
        assert result == "manager_key"

        # Explicit key overrides manager
        result = resolve_api_key(
            user_id="user1",
            provider="gemini",
            explicit_key="explicit_key",
            credential_manager=manager,
        )
        assert result == "explicit_key"

    def test_unified_key_strips_whitespace(self) -> None:
        """Test that unified key strips whitespace."""
        with patch.dict(os.environ, {"AI_API_KEY": "  unified_with_spaces  "}, clear=True):
            result = resolve_api_key(
                user_id="user1",
                provider="gemini",
            )
            assert result == "unified_with_spaces"

    def test_provider_key_strips_whitespace(self) -> None:
        """Test that provider key strips whitespace."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "  provider_with_spaces  "}):
            result = resolve_api_key(
                user_id="user1",
                provider="gemini",
            )
            assert result == "provider_with_spaces"
