"""Integration tests for Gemini service."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from gemini_service.main import app

client = TestClient(app)


class TestGenerateResponseIntegration:
    """Test complete generate response flow."""

    def test_complete_message_flow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test complete flow from request to response."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.return_value = "AI response"

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "What is AI?",
                    "system_prompt": "You are helpful",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "AI response"
        mock_service.generate_response.assert_called_once()

    def test_message_with_schema_flow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test flow with structured output schema."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.return_value = {"answer": "42"}

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "What is the answer?",
                    "system_prompt": "You are helpful",
                    "response_schema": {"type": "object"},
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["output"], dict)

    def test_dependency_injection_works(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that dependency injection is working."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Response"

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service) as mock_get_client:
            client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                },
            )

            mock_get_client.assert_called_once_with(api_key="test_key")


class TestErrorHandlingIntegration:
    """Test error handling scenarios."""

    def test_missing_user_input_returns_400(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing user_input returns 400."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        response = client.post(
            "/generate",
            json={
                "user_input": "",
                "system_prompt": "You are helpful",
            },
        )

        assert response.status_code == 400

    def test_missing_system_prompt_returns_400(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing system_prompt returns 400."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        response = client.post(
            "/generate",
            json={
                "user_input": "Hello",
                "system_prompt": "",
            },
        )

        assert response.status_code == 400

    def test_missing_api_key_returns_500(self) -> None:
        """Test that missing API key returns 500."""
        response = client.post(
            "/generate",
            json={
                "user_input": "Hello",
                "system_prompt": "You are helpful",
            },
        )

        assert response.status_code == 500

    def test_service_value_error_returns_400(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that ValueError from service returns 400."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.side_effect = ValueError("Invalid")

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                },
            )

        assert response.status_code == 400

    def test_service_runtime_error_returns_500(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that RuntimeError from service returns 500."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.side_effect = RuntimeError("API error")

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                },
            )

        assert response.status_code == 500


class TestRequestValidation:
    """Test request validation."""

    def test_request_without_schema(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that request without schema works."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Response"

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                },
            )

        assert response.status_code == 200

    def test_request_with_null_schema(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that null schema works."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Response"

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                    "response_schema": None,
                },
            )

        assert response.status_code == 200

    def test_special_characters_in_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test input with special characters."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        special_input = "Hello! @#$%^&*() 你好"

        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Response"

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": special_input,
                    "system_prompt": "You are helpful",
                },
            )

        assert response.status_code == 200
