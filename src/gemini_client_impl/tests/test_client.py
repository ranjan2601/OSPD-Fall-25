"""Tests for the Gemini client implementation."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import ai_client_api
import gemini_client_impl
from gemini_client_impl.client import GeminiClient, get_client_impl, register


class TestGeminiClientInit:
    """Test GeminiClient initialization."""

    def test_init_with_valid_api_key(self) -> None:
        """Test initializing with a valid API key."""
        with patch("gemini_client_impl.client.genai") as mock_genai:
            client = GeminiClient(api_key="test-key")
            assert client.api_key == "test-key"
            mock_genai.configure.assert_called_once_with(api_key="test-key")

    def test_init_with_empty_api_key(self) -> None:
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError, match="api_key cannot be empty"):
            GeminiClient(api_key="")

    def test_init_configures_genai(self) -> None:
        """Test that initialization configures the Gemini API."""
        with patch("gemini_client_impl.client.genai") as mock_genai:
            GeminiClient(api_key="test-key")
            mock_genai.configure.assert_called_once_with(api_key="test-key")
            mock_genai.GenerativeModel.assert_called_once_with("gemini-2.0-flash")


class TestGeminiClientSendMessage:
    """Test send_message method."""

    @pytest.fixture
    def client(self) -> GeminiClient:
        """Provide a mocked Gemini client for testing."""
        with patch("gemini_client_impl.client.genai.GenerativeModel"):
            client = GeminiClient(api_key="test-key")
            mock_response = MagicMock()
            mock_response.text = "This is a mock response"
            client.model.generate_content = MagicMock(return_value=mock_response)
            return client

    def test_send_message_success(self, client: GeminiClient) -> None:
        """Test sending a message successfully."""
        response = client.send_message("user123", "Hello")
        assert response == "This is a mock response"
        client.model.generate_content.assert_called_once_with("Hello")

    def test_send_message_with_context(self, client: GeminiClient) -> None:
        """Test sending a message with context."""
        context: dict[str, Any] = {"tools": [{"name": "search"}]}
        response = client.send_message("user123", "Hello", context=context)
        assert response == "This is a mock response"

    def test_send_message_empty_user_id(self, client: GeminiClient) -> None:
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            client.send_message("", "Hello")

    def test_send_message_empty_prompt(self, client: GeminiClient) -> None:
        """Test that empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            client.send_message("user123", "")

    def test_send_message_api_error(self, client: GeminiClient) -> None:
        """Test that API errors are wrapped in RuntimeError."""
        client.model.generate_content.side_effect = Exception("API failed")
        with pytest.raises(RuntimeError, match="Error calling Gemini API"):
            client.send_message("user123", "Hello")

    def test_send_message_empty_response(self, client: GeminiClient) -> None:
        """Test handling of empty response from API."""
        mock_response = MagicMock()
        mock_response.text = None
        client.model.generate_content.return_value = mock_response

        response = client.send_message("user123", "Hello")
        assert response == ""


class TestGeminiClientExtractToolCalls:
    """Test extract_tool_calls method."""

    @pytest.fixture
    def client(self) -> GeminiClient:
        """Provide a mocked Gemini client for testing."""
        with patch("gemini_client_impl.client.genai.GenerativeModel"):
            return GeminiClient(api_key="test-key")

    def test_extract_tool_calls_returns_empty_list(self, client: GeminiClient) -> None:
        """Test that extract_tool_calls returns empty list (stub)."""
        result = client.extract_tool_calls("Some response text")
        assert result == []
        assert isinstance(result, list)


class TestFactoryFunction:
    """Test the factory function."""

    def test_get_client_impl_returns_gemini_client(self) -> None:
        """Test that get_client_impl returns a GeminiClient."""
        with patch("gemini_client_impl.client.genai"):
            client = get_client_impl(user_id="user123", api_key="test-key")
            assert isinstance(client, GeminiClient)
            assert client.api_key == "test-key"


class TestDependencyInjection:
    """Test the dependency injection registration."""

    def test_register_sets_get_client(self) -> None:
        """Test that register() sets ai_client_api.get_client."""
        original = ai_client_api.get_client
        try:
            register()
            assert ai_client_api.get_client == get_client_impl
        finally:
            ai_client_api.get_client = original

    def test_module_import_triggers_registration(self) -> None:
        """Test that importing gemini_client_impl and calling register works."""
        original = ai_client_api.get_client
        try:
            gemini_client_impl.register()
            with patch("gemini_client_impl.client.genai"):
                client = ai_client_api.get_client(user_id="user", api_key="key")
                assert isinstance(client, GeminiClient)
        finally:
            ai_client_api.get_client = original
