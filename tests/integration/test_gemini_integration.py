"""Integration tests for Gemini AI Chat Service.

Tests component interactions with mocked dependencies to verify:
- Interface contracts
- Message handling
- Tool call support
- Error handling
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from ai_client_api.client import AIService
from gemini_client_impl.client import GeminiClient

pytestmark = [pytest.mark.integration, pytest.mark.circleci]


@pytest.fixture
def unique_user_id() -> str:
    """Generate unique user_id for test isolation."""
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def mock_gemini_api_key() -> str:
    """Provide a mock API key for testing."""
    return "test_api_key_" + uuid.uuid4().hex[:16]


class TestGeminiClientInterfaceContract:
    """Test that GeminiClient properly implements AIService interface."""

    def test_gemini_client_implements_ai_service(self, mock_gemini_api_key: str) -> None:
        """Verify GeminiClient implements AIService interface."""
        with patch("gemini_client_impl.client.genai"):
            client = GeminiClient(api_key=mock_gemini_api_key)
            assert isinstance(client, AIService)

    def test_gemini_client_has_required_methods(self, mock_gemini_api_key: str) -> None:
        """Verify all required methods exist."""
        with patch("gemini_client_impl.client.genai"):
            client = GeminiClient(api_key=mock_gemini_api_key)
            assert hasattr(client, "send_message")
            assert hasattr(client, "extract_tool_calls")

    def test_gemini_client_method_signatures(self, mock_gemini_api_key: str) -> None:
        """Check method signatures match interface."""
        import inspect

        with patch("gemini_client_impl.client.genai"):
            client = GeminiClient(api_key=mock_gemini_api_key)

            sig = inspect.signature(client.send_message)
            assert "user_id" in sig.parameters
            assert "prompt" in sig.parameters
            assert "context" in sig.parameters

            sig = inspect.signature(client.extract_tool_calls)
            assert "response" in sig.parameters


class TestGeminiClientMessageHandling:
    """Test message sending and handling with mocked Gemini API."""

    def test_send_message_with_mocked_api(
        self,
        mock_gemini_api_key: str,
        unique_user_id: str,
    ) -> None:
        """Send message to mocked Gemini API and verify response structure."""
        with patch("gemini_client_impl.client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "This is a mocked AI response"
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            client = GeminiClient(api_key=mock_gemini_api_key)
            response = client.send_message(unique_user_id, "Hello AI")

            assert response == "This is a mocked AI response"
            mock_model.generate_content.assert_called_once_with("Hello AI")

    def test_send_message_with_context(
        self,
        mock_gemini_api_key: str,
        unique_user_id: str,
    ) -> None:
        """Send message with context and verify it's handled."""
        with patch("gemini_client_impl.client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Response with context"
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            client = GeminiClient(api_key=mock_gemini_api_key)
            context = {"tools": [{"name": "search"}]}
            response = client.send_message(unique_user_id, "Search for info", context=context)

            assert response == "Response with context"

    def test_response_structure_validation(
        self,
        mock_gemini_api_key: str,
        unique_user_id: str,
    ) -> None:
        """Validate the response structure from send_message."""
        with patch("gemini_client_impl.client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Test response"
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            client = GeminiClient(api_key=mock_gemini_api_key)
            response = client.send_message(unique_user_id, "Hello")

            assert isinstance(response, str)
            assert len(response) > 0


class TestGeminiClientToolCalls:
    """Test tool call extraction."""

    def test_extract_tool_calls_returns_list(self, mock_gemini_api_key: str) -> None:
        """Verify extract_tool_calls returns a list."""
        with patch("gemini_client_impl.client.genai"):
            client = GeminiClient(api_key=mock_gemini_api_key)
            result = client.extract_tool_calls("Some response")

            assert isinstance(result, list)

    def test_extract_tool_calls_empty_for_text_response(
        self,
        mock_gemini_api_key: str,
    ) -> None:
        """Verify extract_tool_calls returns empty list for plain text."""
        with patch("gemini_client_impl.client.genai"):
            client = GeminiClient(api_key=mock_gemini_api_key)
            result = client.extract_tool_calls("Just a plain text response")

            assert result == []


class TestGeminiClientMultiUser:
    """Test multi-user scenarios."""

    def test_multiple_users_can_send_messages(self, mock_gemini_api_key: str) -> None:
        """Multiple users can send messages independently."""
        users = [f"user_{i}_{uuid.uuid4().hex[:4]}" for i in range(3)]

        with patch("gemini_client_impl.client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.return_value = MagicMock(text="Response")
            mock_genai.GenerativeModel.return_value = mock_model

            client = GeminiClient(api_key=mock_gemini_api_key)

            for user in users:
                response = client.send_message(user, f"Message from {user}")
                assert response == "Response"

            assert mock_model.generate_content.call_count == 3


class TestGeminiErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_user_id_handling(self, mock_gemini_api_key: str) -> None:
        """Test handling of invalid user_id."""
        with patch("gemini_client_impl.client.genai"):
            client = GeminiClient(api_key=mock_gemini_api_key)

            with pytest.raises(ValueError, match="user_id cannot be empty"):
                client.send_message("", "Message")

    def test_empty_prompt_handling(
        self,
        mock_gemini_api_key: str,
        unique_user_id: str,
    ) -> None:
        """Test handling of empty prompts."""
        with patch("gemini_client_impl.client.genai"):
            client = GeminiClient(api_key=mock_gemini_api_key)

            with pytest.raises(ValueError, match="prompt cannot be empty"):
                client.send_message(unique_user_id, "")

    def test_api_error_handling(
        self,
        mock_gemini_api_key: str,
        unique_user_id: str,
    ) -> None:
        """Test handling of API errors."""
        with patch("gemini_client_impl.client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = Exception("API Error")
            mock_genai.GenerativeModel.return_value = mock_model

            client = GeminiClient(api_key=mock_gemini_api_key)

            with pytest.raises(RuntimeError, match="Error calling Gemini API"):
                client.send_message(unique_user_id, "Test message")

    def test_empty_api_key_rejected(self) -> None:
        """Test that empty API key is rejected."""
        with pytest.raises(ValueError, match="api_key cannot be empty"):
            GeminiClient(api_key="")

    def test_none_response_handled(
        self,
        mock_gemini_api_key: str,
        unique_user_id: str,
    ) -> None:
        """Test handling of None response from API."""
        with patch("gemini_client_impl.client.genai") as mock_genai:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = None
            mock_model.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_model

            client = GeminiClient(api_key=mock_gemini_api_key)
            response = client.send_message(unique_user_id, "Test")

            assert response == ""
