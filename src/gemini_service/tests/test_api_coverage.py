"""Additional tests for Gemini service API to improve coverage."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from gemini_service.main import app

client = TestClient(app)


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint(self) -> None:
        """Test root endpoint returns service status."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Gemini AI Service is running"


class TestAPIKeyErrorHandling:
    """Test API key resolution error handling."""

    def test_resolve_api_key_value_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that ValueError from resolve_api_key returns 500."""
        # Don't set GEMINI_API_KEY to trigger ValueError
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        with patch("gemini_service.api.resolve_api_key") as mock_resolve:
            # Make resolve_api_key raise ValueError
            mock_resolve.side_effect = ValueError("No API key configured for provider 'gemini'")

            response = client.post(
                "/generate",
                json={
                    "user_input": "Hello",
                    "system_prompt": "You are helpful",
                },
            )

            assert response.status_code == 500
            assert "No API key configured" in response.json()["detail"]
            mock_resolve.assert_called_once_with(user_id="service", provider="gemini")
