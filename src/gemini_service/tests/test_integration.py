"""Integration tests for gemini_service.

Tests the complete flow from HTTP request through the service.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from gemini_service.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check and status endpoints."""

    def test_root_endpoint_returns_service_status(self, client: TestClient) -> None:
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "Gemini AI Service" in response.json()["message"]

    def test_health_endpoint_returns_healthy(self, client: TestClient) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Gemini AI Service"
        assert data["version"] == "1.0.0"


class TestSendMessageIntegration:
    """Integration tests for the /send_message endpoint."""

    def test_complete_message_flow(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test complete flow of sending a message and receiving response."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.return_value = "This is the AI response"
        mock_service.extract_tool_calls.return_value = []

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = client.post(
                "/send_message",
                json={
                    "user_id": "integration_user",
                    "prompt": "What is machine learning?",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "tool_calls" in data
        assert data["text"] == "This is the AI response"
        assert data["tool_calls"] == []

    def test_message_with_tools_flow(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test flow with tool definitions passed."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_tool_call = MagicMock()
        mock_tool_call.tool_name = "search"
        mock_tool_call.tool_args = {"query": "latest news"}
        mock_tool_call.tool_id = "call_001"

        mock_service = MagicMock()
        mock_service.send_message.return_value = "Searching for news"
        mock_service.extract_tool_calls.return_value = [mock_tool_call]

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = client.post(
                "/send_message",
                json={
                    "user_id": "tool_user",
                    "prompt": "Search for the latest news",
                    "tools": [
                        {
                            "name": "search",
                            "description": "Search the web",
                            "parameters": {"query": {"type": "string"}},
                        },
                    ],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Searching for news"
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["tool_name"] == "search"
        assert data["tool_calls"][0]["tool_args"]["query"] == "latest news"

    def test_dependency_injection_works(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that DI properly injects the Gemini implementation."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.return_value = "Response"
        mock_service.extract_tool_calls.return_value = []

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ) as mock_get_client:
            client.post(
                "/send_message",
                json={"user_id": "test_user", "prompt": "Hello"},
            )

            mock_get_client.assert_called_once_with(
                user_id="test_user",
                api_key="test_key",
            )


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""

    def test_missing_user_id_returns_400(self, client: TestClient) -> None:
        """Test that missing user_id returns proper error."""
        response = client.post(
            "/send_message",
            json={"user_id": "", "prompt": "Hello"},
        )
        assert response.status_code == 400
        assert "user_id" in response.json()["detail"]

    def test_missing_prompt_returns_400(self, client: TestClient) -> None:
        """Test that missing prompt returns proper error."""
        response = client.post(
            "/send_message",
            json={"user_id": "user", "prompt": ""},
        )
        assert response.status_code == 400
        assert "prompt" in response.json()["detail"]

    def test_missing_api_key_returns_500(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that missing API key returns proper error."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        response = client.post(
            "/send_message",
            json={"user_id": "user", "prompt": "Hello"},
        )
        assert response.status_code == 500
        assert "GEMINI_API_KEY" in response.json()["detail"]

    def test_service_value_error_returns_400(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that ValueError from service returns 400."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.side_effect = ValueError("Bad input")

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = client.post(
                "/send_message",
                json={"user_id": "user", "prompt": "Hello"},
            )

        assert response.status_code == 400
        assert "Bad input" in response.json()["detail"]

    def test_service_runtime_error_returns_500(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that RuntimeError from service returns 500."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.side_effect = RuntimeError("API failed")

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = client.post(
                "/send_message",
                json={"user_id": "user", "prompt": "Hello"},
            )

        assert response.status_code == 500
        assert "API failed" in response.json()["detail"]


class TestRequestValidation:
    """Test request validation and edge cases."""

    def test_request_without_tools(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that tools field is optional."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.return_value = "Response"
        mock_service.extract_tool_calls.return_value = []

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = client.post(
                "/send_message",
                json={"user_id": "user", "prompt": "Hello"},
            )

        assert response.status_code == 200
        mock_service.send_message.assert_called_once()
        call_kwargs = mock_service.send_message.call_args.kwargs
        assert call_kwargs["context"] is None

    def test_request_with_empty_tools_list(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that empty tools list works."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.return_value = "Response"
        mock_service.extract_tool_calls.return_value = []

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = client.post(
                "/send_message",
                json={"user_id": "user", "prompt": "Hello", "tools": []},
            )

        assert response.status_code == 200

    def test_special_characters_in_prompt(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test prompts with special characters."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        special_prompt = "Hello! @#$%^&*() 你好"

        mock_service = MagicMock()
        mock_service.send_message.return_value = "Response"
        mock_service.extract_tool_calls.return_value = []

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = client.post(
                "/send_message",
                json={"user_id": "user", "prompt": special_prompt},
            )

        assert response.status_code == 200
        mock_service.send_message.assert_called_once()
        call_kwargs = mock_service.send_message.call_args.kwargs
        assert call_kwargs["prompt"] == special_prompt
