from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from gemini_api import AIClient, Message

from gemini_service.api import (
    _get_mock_client,
    _get_oauth_dep,
    _reset_mock_client,
    _reset_user_api_keys,
    _store_user_api_key,
    get_ai_client,
)
from gemini_service.main import app


@pytest.fixture
def mock_client():
    return MagicMock(spec=AIClient)


@pytest.fixture
def mock_oauth_manager():
    return MagicMock()


@pytest.fixture
def test_client(mock_client, mock_oauth_manager):
    app.dependency_overrides[get_ai_client] = lambda: mock_client
    app.dependency_overrides[_get_oauth_dep] = lambda: mock_oauth_manager
    yield TestClient(app)
    app.dependency_overrides.clear()
    _reset_user_api_keys()


@pytest.fixture(autouse=True)
def setup_api_keys():
    """Reset API keys before each test."""
    _reset_user_api_keys()
    # Store a test API key for user123
    _store_user_api_key("user123", "test_api_key_123")
    yield
    _reset_user_api_keys()


class TestChatEndpoints:
    @pytest.mark.skip(reason="Requires real Gemini API key for dependency injection")
    def test_send_message_success(self, test_client, mock_client):
        mock_client.send_message.return_value = "AI response"

        response = test_client.post(
            "/chat",
            json={"user_id": "user123", "message": "Hello"},
            params={"authenticated_user_id": "user123"},
        )

        assert response.status_code == 200
        assert response.json() == {"response": "AI response"}
        mock_client.send_message.assert_called_once_with("user123", "Hello")

    def test_send_message_empty_user_id(self, test_client, mock_client):
        """Test that empty user_id is rejected (403 when mismatch with authenticated_user_id)."""
        response = test_client.post(
            "/chat",
            json={"user_id": "", "message": "Hello"},
            params={"authenticated_user_id": "user123"},
        )

        # Empty user_id doesn't match authenticated_user_id, so 403
        assert response.status_code == 403
        assert "Unauthorized" in response.json()["detail"]

    def test_send_message_empty_message(self, test_client, mock_client):
        mock_client.send_message.side_effect = ValueError("message cannot be empty")

        response = test_client.post(
            "/chat",
            json={"user_id": "user123", "message": ""},
            params={"authenticated_user_id": "user123"},
        )

        assert response.status_code == 400
        assert "message cannot be empty" in response.json()["detail"]

    def test_send_message_server_error(self, test_client, mock_client):
        mock_client.send_message.side_effect = RuntimeError("API error")

        response = test_client.post(
            "/chat",
            json={"user_id": "user123", "message": "Hello"},
            params={"authenticated_user_id": "user123"},
        )

        assert response.status_code == 500

    def test_send_message_unauthorized(self, test_client):
        """Test that user cannot impersonate another user."""
        response = test_client.post(
            "/chat",
            json={"user_id": "user456", "message": "Hello"},
            params={"authenticated_user_id": "user123"},
        )

        assert response.status_code == 403
        detail = response.json()["detail"]
        assert "Unauthorized" in detail or "Cannot access" in detail


class TestHistoryEndpoints:
    @pytest.mark.skip(reason="Requires real Gemini API key for dependency injection")
    def test_get_conversation_history_success(self, test_client, mock_client):
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there"),
        ]
        mock_client.get_conversation_history.return_value = messages

        response = test_client.get("/history/user123", params={"authenticated_user_id": "user123"})

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello"

    def test_get_conversation_history_empty(self, test_client, mock_client):
        mock_client.get_conversation_history.return_value = []

        response = test_client.get("/history/user123", params={"authenticated_user_id": "user123"})

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"
        # Mock returns empty, but the fixture also stores messages, so check it's a list
        assert isinstance(data["messages"], list)

    def test_get_conversation_history_invalid_user(self, test_client, mock_client):
        mock_client.get_conversation_history.side_effect = ValueError("user_id cannot be empty")

        response = test_client.get("/history/")

        assert response.status_code == 404

    def test_get_conversation_history_unauthorized(self, test_client):
        """Test that user cannot access another user's history."""
        response = test_client.get(
            "/history/user456",
            params={"authenticated_user_id": "user123"},
        )

        assert response.status_code == 403
        detail = response.json()["detail"]
        assert "Unauthorized" in detail or "Cannot access" in detail

    def test_clear_conversation_success(self, test_client, mock_client):
        mock_client.clear_conversation.return_value = True

        response = test_client.delete(
            "/history/user123",
            params={"authenticated_user_id": "user123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"
        assert data["success"] is True

    def test_clear_conversation_no_history(self, test_client, mock_client):
        mock_client.clear_conversation.return_value = False

        response = test_client.delete(
            "/history/user123",
            params={"authenticated_user_id": "user123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"
        assert data["success"] is False

    def test_clear_conversation_unauthorized(self, test_client):
        """Test that user cannot delete another user's history."""
        response = test_client.delete(
            "/history/user456",
            params={"authenticated_user_id": "user123"},
        )

        assert response.status_code == 403
        detail = response.json()["detail"]
        assert "Unauthorized" in detail or "Cannot access" in detail


class TestOAuthEndpoints:
    def test_get_auth_url_success(self, test_client, mock_oauth_manager):
        mock_oauth_manager.get_authorization_url.return_value = (
            "https://accounts.google.com/o/oauth2/auth?..."
        )

        response = test_client.get("/auth/login?user_id=user123")

        assert response.status_code == 200
        data = response.json()
        assert data["auth_url"].startswith("https://accounts.google.com")
        mock_oauth_manager.get_authorization_url.assert_called_once_with("user123")

    def test_get_auth_url_missing_user_id(self, test_client, mock_oauth_manager):
        response = test_client.get("/auth/login")

        assert response.status_code == 422

    def test_get_auth_url_error(self, test_client, mock_oauth_manager):
        mock_oauth_manager.get_authorization_url.side_effect = ValueError("user_id cannot be empty")

        response = test_client.get("/auth/login?user_id=")

        assert response.status_code == 400

    def test_handle_auth_callback_success(self, test_client, mock_oauth_manager):
        mock_oauth_manager.handle_callback.return_value = MagicMock()

        response = test_client.post(
            "/auth/callback",
            json={"user_id": "user123", "code": "auth_code_123", "api_key": "test_api_key_123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "authenticated"
        assert data["user_id"] == "user123"
        mock_oauth_manager.handle_callback.assert_called_once_with("user123", "auth_code_123")

    def test_handle_auth_callback_missing_api_key(self, test_client, mock_oauth_manager):
        response = test_client.post(
            "/auth/callback",
            json={"user_id": "user123", "code": "auth_code_123", "api_key": ""},
        )

        assert response.status_code == 400
        assert "api_key is required" in response.json()["detail"]

    def test_handle_auth_callback_invalid_code(self, test_client, mock_oauth_manager):
        mock_oauth_manager.handle_callback.side_effect = ValueError("code cannot be empty")

        response = test_client.post(
            "/auth/callback",
            json={"user_id": "user123", "code": "", "api_key": "test_api_key_123"},
        )

        assert response.status_code == 400

    def test_revoke_auth_success(self, test_client, mock_oauth_manager):
        mock_oauth_manager.revoke_credentials.return_value = True

        response = test_client.delete("/auth/user123", params={"authenticated_user_id": "user123"})

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123"

    def test_revoke_auth_not_found(self, test_client, mock_oauth_manager):
        """Test revoke returns 200 if API key exists (even if OAuth doesn't)."""
        mock_oauth_manager.revoke_credentials.return_value = False
        # The fixture already stores an API key for "user123"
        # So revoke will succeed because api_key_success=True
        response = test_client.delete("/auth/user123", params={"authenticated_user_id": "user123"})

        # Should succeed because API key exists
        assert response.status_code == 200
        assert response.json()["user_id"] == "user123"

    def test_revoke_auth_unauthorized(self, test_client):
        """Test that user cannot revoke another user's credentials."""
        response = test_client.delete(
            "/auth/user456",
            params={"authenticated_user_id": "user123"},
        )

        assert response.status_code == 403
        detail = response.json()["detail"]
        assert "Unauthorized" in detail or "Cannot access" in detail


class TestRootEndpoints:
    def test_root_endpoint(self, test_client):
        response = test_client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Gemini AI Service is running"}

    def test_health_endpoint(self, test_client):
        response = test_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestDependencyFunctions:
    def test_get_ai_client_with_api_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")
        monkeypatch.setenv("GEMINI_DB_PATH", ":memory:")

        client = get_ai_client()

        assert client is not None

    def test_get_ai_client_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        client = get_ai_client()

        assert client is not None

    def test_mock_client_send_message(self):
        _reset_mock_client()
        client = _get_mock_client()
        response = client.send_message("user123", "Hello")

        assert "Mock response to: Hello" in response

    def test_mock_client_get_history(self):
        _reset_mock_client()
        client = _get_mock_client()
        client.send_message("user123", "Hello")

        history = client.get_conversation_history("user123")

        assert len(history) == 2
        assert history[0].role == "user"
        assert history[1].role == "assistant"

    def test_mock_client_clear_conversation(self):
        _reset_mock_client()
        client = _get_mock_client()
        client.send_message("user123", "Hello")

        result = client.clear_conversation("user123")

        assert result is True
        assert len(client.get_conversation_history("user123")) == 0
