"""Tests for the Gemini AI service API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from gemini_service.main import app


@pytest.fixture
def test_client() -> TestClient:
    """Fixture providing a TestClient."""
    return TestClient(app)


class TestRootEndpoints:
    """Tests for root and health endpoints."""

    def test_root_endpoint(self, test_client: TestClient) -> None:
        """Test the root endpoint returns service status."""
        response = test_client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Gemini AI Service is running"}

    def test_health_endpoint(self, test_client: TestClient) -> None:
        """Test the health check endpoint returns healthy status."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Gemini AI Service"
        assert data["version"] == "1.0.0"


class TestSendMessageEndpoint:
    """Tests for the /send_message endpoint."""

    def test_send_message_success(
        self,
        test_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test successful message sending."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.return_value = "AI response"
        mock_service.extract_tool_calls.return_value = []

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = test_client.post(
                "/send_message",
                json={"user_id": "user123", "prompt": "Hello"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "AI response"
        assert data["tool_calls"] == []

    def test_send_message_empty_user_id(self, test_client: TestClient) -> None:
        """Test that empty user_id returns 400."""
        response = test_client.post(
            "/send_message",
            json={"user_id": "", "prompt": "Hello"},
        )

        assert response.status_code == 400
        assert "user_id is required" in response.json()["detail"]

    def test_send_message_empty_prompt(self, test_client: TestClient) -> None:
        """Test that empty prompt returns 400."""
        response = test_client.post(
            "/send_message",
            json={"user_id": "user123", "prompt": ""},
        )

        assert response.status_code == 400
        assert "prompt is required" in response.json()["detail"]

    def test_send_message_missing_api_key(
        self,
        test_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that missing API key returns 500."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        response = test_client.post(
            "/send_message",
            json={"user_id": "user123", "prompt": "Hello"},
        )

        assert response.status_code == 500
        assert "GEMINI_API_KEY" in response.json()["detail"]

    def test_send_message_with_tools(
        self,
        test_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test sending a message with tool definitions."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.return_value = "I'll close that ticket"
        mock_service.extract_tool_calls.return_value = []

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = test_client.post(
                "/send_message",
                json={
                    "user_id": "user123",
                    "prompt": "Close ticket 123",
                    "tools": [
                        {
                            "name": "close_ticket",
                            "description": "Close a support ticket",
                            "parameters": {"ticket_id": {"type": "string"}},
                        },
                    ],
                },
            )

        assert response.status_code == 200
        mock_service.send_message.assert_called_once()
        call_args = mock_service.send_message.call_args
        assert call_args.kwargs["context"] is not None
        assert "tools" in call_args.kwargs["context"]

    def test_send_message_with_tool_calls_response(
        self,
        test_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that tool calls are extracted and returned."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_tool_call = MagicMock()
        mock_tool_call.tool_name = "close_ticket"
        mock_tool_call.tool_args = {"ticket_id": "123"}
        mock_tool_call.tool_id = "tc_001"

        mock_service = MagicMock()
        mock_service.send_message.return_value = "Closing ticket"
        mock_service.extract_tool_calls.return_value = [mock_tool_call]

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = test_client.post(
                "/send_message",
                json={"user_id": "user123", "prompt": "Close ticket 123"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Closing ticket"
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["tool_name"] == "close_ticket"
        assert data["tool_calls"][0]["tool_args"] == {"ticket_id": "123"}
        assert data["tool_calls"][0]["tool_id"] == "tc_001"

    def test_send_message_value_error(
        self,
        test_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that ValueError from service returns 400."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.side_effect = ValueError("Invalid input")

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = test_client.post(
                "/send_message",
                json={"user_id": "user123", "prompt": "Hello"},
            )

        assert response.status_code == 400
        assert "Invalid input" in response.json()["detail"]

    def test_send_message_runtime_error(
        self,
        test_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that RuntimeError from service returns 500."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.side_effect = RuntimeError("API error")

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = test_client.post(
                "/send_message",
                json={"user_id": "user123", "prompt": "Hello"},
            )

        assert response.status_code == 500
        assert "API error" in response.json()["detail"]

    def test_send_message_unexpected_error(
        self,
        test_client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that unexpected exceptions return 500."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.send_message.side_effect = Exception("Unexpected error")

        with patch(
            "gemini_service.api.ai_client_api.get_client",
            return_value=mock_service,
        ):
            response = test_client.post(
                "/send_message",
                json={"user_id": "user123", "prompt": "Hello"},
            )

        assert response.status_code == 500
        assert "Error sending message" in response.json()["detail"]
