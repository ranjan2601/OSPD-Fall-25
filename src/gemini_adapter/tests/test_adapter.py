"""Tests for the Gemini service adapter."""

from unittest.mock import MagicMock, patch

import pytest

from ai_client_api.client import AIService
from gemini_adapter import GeminiServiceAdapter


class TestGeminiServiceAdapterInitialization:
    """Test adapter initialization."""

    def test_init_with_default_url(self) -> None:
        """Test initializing with default URL."""
        with patch(
            "gemini_adapter._impl.GeminiHTTPClient",
        ) as mock_client_class:
            adapter = GeminiServiceAdapter()
            mock_client_class.assert_called_once_with(base_url="http://127.0.0.1:8000")
            assert adapter.client is not None

    def test_init_with_custom_url(self) -> None:
        """Test initializing with custom URL."""
        with patch(
            "gemini_adapter._impl.GeminiHTTPClient",
        ) as mock_client_class:
            GeminiServiceAdapter(base_url="http://example.com:9000")
            mock_client_class.assert_called_once_with(base_url="http://example.com:9000")

    def test_implements_ai_service_interface(self) -> None:
        """Test that adapter implements AIService interface."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()
            assert isinstance(adapter, AIService)


class TestSendMessage:
    """Test send_message method."""

    def test_send_message_success(self) -> None:
        """Test sending a message successfully."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_response = MagicMock()
            mock_response.text = "Test response"
            mock_client_instance.send_message_send_message_post.return_value = mock_response

            adapter = GeminiServiceAdapter()
            result = adapter.send_message("user123", "Hello")

            assert result == "Test response"
            mock_client_instance.send_message_send_message_post.assert_called_once_with(
                json_body={"user_id": "user123", "prompt": "Hello"},
            )

    def test_send_message_with_context(self) -> None:
        """Test sending a message with context."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_response = MagicMock()
            mock_response.text = "Response with tools"
            mock_client_instance.send_message_send_message_post.return_value = mock_response

            adapter = GeminiServiceAdapter()
            context = {"tools": [{"name": "search", "description": "Search"}]}
            result = adapter.send_message("user123", "Hello", context=context)

            assert result == "Response with tools"
            mock_client_instance.send_message_send_message_post.assert_called_once_with(
                json_body={
                    "user_id": "user123",
                    "prompt": "Hello",
                    "tools": [{"name": "search", "description": "Search"}],
                },
            )

    def test_send_message_empty_user_id(self) -> None:
        """Test that empty user_id raises ValueError."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()

            with pytest.raises(ValueError, match="user_id cannot be empty"):
                adapter.send_message("", "Hello")

    def test_send_message_empty_prompt(self) -> None:
        """Test that empty prompt raises ValueError."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()

            with pytest.raises(ValueError, match="prompt cannot be empty"):
                adapter.send_message("user123", "")


class TestExtractToolCalls:
    """Test extract_tool_calls method."""

    def test_extract_tool_calls_returns_empty_list(self) -> None:
        """Test that extract_tool_calls returns empty list."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()
            result = adapter.extract_tool_calls("Some response")
            assert result == []
            assert isinstance(result, list)
