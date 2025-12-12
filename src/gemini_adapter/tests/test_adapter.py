"""Tests for the Gemini service adapter."""

from unittest.mock import MagicMock, patch

import pytest

from ai_client_api.client import AIInterface
from gemini_adapter import GeminiServiceAdapter


class TestGeminiServiceAdapterInitialization:
    """Test adapter initialization."""

    def test_init_with_default_url(self) -> None:
        """Test initializing with default URL."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            adapter = GeminiServiceAdapter()
            mock_client_class.assert_called_once_with(base_url="http://127.0.0.1:8000")
            assert adapter.client is not None

    def test_init_with_custom_url(self) -> None:
        """Test initializing with custom URL."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            GeminiServiceAdapter(base_url="http://example.com:9000")
            mock_client_class.assert_called_once_with(base_url="http://example.com:9000")

    def test_implements_ai_interface(self) -> None:
        """Test that adapter implements AIInterface."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()
            assert isinstance(adapter, AIInterface)


class TestGenerateResponse:
    """Test generate_response method."""

    def test_generate_response_success(self) -> None:
        """Test generating a response successfully."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_response = MagicMock()
            mock_response.output = "Test response"
            mock_client_instance.generate_response_generate_post.return_value = mock_response

            adapter = GeminiServiceAdapter()
            result = adapter.generate_response("Hello", "You are helpful")

            assert result == "Test response"
            mock_client_instance.generate_response_generate_post.assert_called_once()

    def test_generate_response_empty_user_input(self) -> None:
        """Test that empty user_input raises ValueError."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()

            with pytest.raises(ValueError, match="user_input cannot be empty"):
                adapter.generate_response("", "You are helpful")

    def test_generate_response_empty_system_prompt(self) -> None:
        """Test that empty system_prompt raises ValueError."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()

            with pytest.raises(ValueError, match="system_prompt cannot be empty"):
                adapter.generate_response("Hello", "")

    def test_generate_response_with_schema(self) -> None:
        """Test generating structured response with schema."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_response = MagicMock()
            mock_response.output = {"result": "structured"}
            mock_client_instance.generate_response_generate_post.return_value = mock_response

            adapter = GeminiServiceAdapter()
            schema = {"type": "object"}
            result = adapter.generate_response("Hello", "You are helpful", schema)

            assert isinstance(result, dict)
            assert result == {"result": "structured"}
