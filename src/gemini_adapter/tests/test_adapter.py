"""Tests for the Gemini service adapter."""

from unittest.mock import MagicMock, patch

import pytest
from gemini_api import AIClient, Message
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

    def test_implements_ai_client_interface(self) -> None:
        """Test that adapter implements AIClient interface."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()
            assert isinstance(adapter, AIClient)


class TestSendMessage:
    """Test send_message method."""

    def test_send_message_success(self) -> None:
        """Test sending a message successfully."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_response = MagicMock()
            mock_response.response = "Test response"
            mock_client_instance.send_message_chat_post.return_value = mock_response

            adapter = GeminiServiceAdapter()
            result = adapter.send_message("user123", "Hello")

            assert result == "Test response"
            mock_client_instance.send_message_chat_post.assert_called_once_with(
                json_body={"user_id": "user123", "message": "Hello"},
            )

    def test_send_message_empty_user_id(self) -> None:
        """Test that empty user_id raises ValueError."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()

            with pytest.raises(ValueError, match="user_id cannot be empty"):
                adapter.send_message("", "Hello")

    def test_send_message_empty_message(self) -> None:
        """Test that empty message raises ValueError."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()

            with pytest.raises(ValueError, match="message cannot be empty"):
                adapter.send_message("user123", "")


class TestGetConversationHistory:
    """Test get_conversation_history method."""

    def test_get_history_success(self) -> None:
        """Test retrieving conversation history successfully."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_msg1 = MagicMock()
            mock_msg1.role = "user"
            mock_msg1.content = "Hello"

            mock_msg2 = MagicMock()
            mock_msg2.role = "assistant"
            mock_msg2.content = "Hi there"

            mock_response = MagicMock()
            mock_response.messages = [mock_msg1, mock_msg2]
            mock_client_instance.get_conversation_history_history_user_id_get.return_value = (
                mock_response
            )

            adapter = GeminiServiceAdapter()
            history = adapter.get_conversation_history("user123")

            assert len(history) == 2
            assert history[0].role == "user"
            assert history[0].content == "Hello"
            assert history[1].role == "assistant"
            assert history[1].content == "Hi there"
            assert isinstance(history[0], Message)
            assert isinstance(history[1], Message)

    def test_get_history_empty_list(self) -> None:
        """Test getting empty conversation history."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_response = MagicMock()
            mock_response.messages = []
            mock_client_instance.get_conversation_history_history_user_id_get.return_value = (
                mock_response
            )

            adapter = GeminiServiceAdapter()
            history = adapter.get_conversation_history("user123")

            assert history == []

    def test_get_history_empty_user_id(self) -> None:
        """Test that empty user_id raises ValueError."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()

            with pytest.raises(ValueError, match="user_id cannot be empty"):
                adapter.get_conversation_history("")


class TestClearConversation:
    """Test clear_conversation method."""

    def test_clear_conversation_success(self) -> None:
        """Test clearing conversation successfully."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_response = MagicMock()
            mock_response.cleared = True
            mock_client_instance.clear_conversation_history_user_id_delete.return_value = (
                mock_response
            )

            adapter = GeminiServiceAdapter()
            result = adapter.clear_conversation("user123")

            assert result is True
            mock_client_instance.clear_conversation_history_user_id_delete.assert_called_once_with(
                user_id="user123",
            )

    def test_clear_conversation_failure(self) -> None:
        """Test clearing conversation when it fails."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_response = MagicMock()
            mock_response.cleared = False
            mock_client_instance.clear_conversation_history_user_id_delete.return_value = (
                mock_response
            )

            adapter = GeminiServiceAdapter()
            result = adapter.clear_conversation("user123")

            assert result is False

    def test_clear_conversation_empty_user_id(self) -> None:
        """Test that empty user_id raises ValueError."""
        with patch("gemini_adapter._impl.GeminiHTTPClient"):
            adapter = GeminiServiceAdapter()

            with pytest.raises(ValueError, match="user_id cannot be empty"):
                adapter.clear_conversation("")

    def test_clear_conversation_response_without_cleared_field(self) -> None:
        """Test clearing when response doesn't have cleared field."""
        with patch("gemini_adapter._impl.GeminiHTTPClient") as mock_client_class:
            mock_client_instance = MagicMock()
            mock_client_class.return_value = mock_client_instance

            mock_response = MagicMock(spec=[])
            mock_client_instance.clear_conversation_history_user_id_delete.return_value = (
                mock_response
            )

            adapter = GeminiServiceAdapter()
            result = adapter.clear_conversation("user123")

            assert result is True
