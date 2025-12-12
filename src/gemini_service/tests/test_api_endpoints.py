"""Tests for Gemini service API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from gemini_service.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_200(self) -> None:
        """Test that health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_correct_data(self) -> None:
        """Test that health check returns correct data."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Gemini AI Service"
        assert "version" in data


class TestGenerateEndpoint:
    """Test generate response endpoint."""

    def test_generate_response_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful response generation."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.return_value = "Test response"

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "Test response"

    def test_generate_response_empty_user_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that empty user_input returns 400."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        response = client.post(
            "/generate",
            json={
                "user_input": "",
                "system_prompt": "You are helpful",
            },
        )

        assert response.status_code == 400
        assert "user_input" in response.json()["detail"]

    def test_generate_response_empty_system_prompt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that empty system_prompt returns 400."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        response = client.post(
            "/generate",
            json={
                "user_input": "Hello",
                "system_prompt": "",
            },
        )

        assert response.status_code == 400
        assert "system_prompt" in response.json()["detail"]

    def test_generate_response_missing_api_key(self) -> None:
        """Test that missing API key returns 500."""
        response = client.post(
            "/generate",
            json={
                "user_input": "Hello",
                "system_prompt": "You are helpful",
            },
        )

        assert response.status_code == 500

    def test_generate_response_with_schema(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test generating structured response with schema."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.return_value = {"result": "structured"}

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                    "response_schema": {"type": "object"},
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["output"], dict)

    def test_generate_response_value_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that ValueError from service returns 400."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.side_effect = ValueError("Invalid input")

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                },
            )

        assert response.status_code == 400

    def test_generate_response_runtime_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
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

    def test_generate_response_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that unexpected error returns 500."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        mock_service = MagicMock()
        mock_service.generate_response.side_effect = Exception("Unexpected")

        with patch("gemini_service.api.ai_client_api.get_client", return_value=mock_service):
            response = client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                },
            )

        assert response.status_code == 500
