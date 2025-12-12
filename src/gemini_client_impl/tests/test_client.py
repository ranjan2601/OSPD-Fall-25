"""Tests for the Gemini client implementation."""

from typing import Generator, Any
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


class TestGeminiClientGenerateResponse:
    """Test generate_response method."""

    @pytest.fixture
    def client(self) -> GeminiClient:
        """Provide a mocked Gemini client for testing."""
        with patch("gemini_client_impl.client.genai.GenerativeModel"):
            client = GeminiClient(api_key="test-key")
            mock_response = MagicMock()
            mock_response.text = "This is a mock response"
            client.model.generate_content = MagicMock(return_value=mock_response)
            return client

    def test_generate_response_success(self, client: GeminiClient) -> None:
        """Test generating a response successfully."""
        response = client.generate_response("Hello", "You are helpful")
        assert response == "This is a mock response"
        client.model.generate_content.assert_called_once()

    def test_generate_response_with_schema(self, client: GeminiClient) -> None:
        """Test generating a structured response with schema."""
        mock_response = MagicMock()
        mock_response.text = '{"result": "structured"}'
        client.model.generate_content = MagicMock(return_value=mock_response)

        schema: dict[str, Any] = {"type": "object"}
        response = client.generate_response("Hello", "You are helpful", schema)
        assert isinstance(response, dict)

    def test_generate_response_empty_user_input(self, client: GeminiClient) -> None:
        """Test that empty user_input raises ValueError."""
        with pytest.raises(ValueError, match="user_input cannot be empty"):
            client.generate_response("", "You are helpful")

    def test_generate_response_empty_system_prompt(self, client: GeminiClient) -> None:
        """Test that empty system_prompt raises ValueError."""
        with pytest.raises(ValueError, match="system_prompt cannot be empty"):
            client.generate_response("Hello", "")

    def test_generate_response_api_error(self, client: GeminiClient) -> None:
        """Test that API errors are wrapped in RuntimeError."""
        client.model.generate_content.side_effect = Exception("API failed")
        with pytest.raises(RuntimeError, match="Error calling Gemini API"):
            client.generate_response("Hello", "You are helpful")

    def test_generate_response_empty_response(self, client: GeminiClient) -> None:
        """Test handling of empty response from API."""
        mock_response = MagicMock()
        mock_response.text = None
        client.model.generate_content = MagicMock(return_value=mock_response)
        response = client.generate_response("Hello", "You are helpful")
        assert response == ""


class TestFactoryFunction:
    """Test factory function."""

    def test_get_client_impl_returns_gemini_client(self) -> None:
        """Test that get_client_impl returns a GeminiClient instance."""
        with patch("gemini_client_impl.client.genai"):
            client = get_client_impl(api_key="test-key")
            assert isinstance(client, GeminiClient)


class TestDependencyInjection:
    """Test dependency injection via register()."""

    @pytest.fixture(autouse=True)
    def save_original_factory(self) -> Generator[None, None, None]:
        """Save and restore original factory."""
        import importlib
        from ai_client_api import client as client_module

        importlib.reload(client_module)
        original = client_module.get_client
        yield
        ai_client_api.get_client = original

    def test_register_function_exists(self) -> None:
        """Test that register() function exists."""
        assert callable(register)

    def test_module_import_triggers_registration(self) -> None:
        """Test that importing module registers the implementation."""
        gemini_client_impl.register()

        with patch("gemini_client_impl.client.genai"):
            client = ai_client_api.get_client(api_key="test-key")
            assert isinstance(client, GeminiClient)
