"""Integration tests for gemini_service.

Tests the complete flow from HTTP request through the service to the client.
"""

import pytest
from fastapi.testclient import TestClient

from gemini_service.api import _get_mock_client, _reset_mock_client
from gemini_service.main import app


@pytest.fixture
def client():
    _reset_mock_client()
    return TestClient(app)


class TestEndToEndChatFlow:
    """Test complete chat conversation flow."""

    @pytest.mark.local_credentials
    def test_complete_conversation_flow(self, client):
        """Test sending multiple messages and retrieving history."""
        user_id = "integration_user_001"

        response1 = client.post(
            "/chat",
            json={"user_id": user_id, "message": "What is AI?"},
        )
        assert response1.status_code == 200
        assert "response" in response1.json()

        response2 = client.post(
            "/chat",
            json={"user_id": user_id, "message": "Tell me more"},
        )
        assert response2.status_code == 200

        history_response = client.get(f"/history/{user_id}")
        assert history_response.status_code == 200
        history = history_response.json()
        assert history["user_id"] == user_id
        assert len(history["messages"]) >= 4

        clear_response = client.delete(f"/history/{user_id}")
        assert clear_response.status_code == 200
        assert clear_response.json()["success"] is True

        empty_history = client.get(f"/history/{user_id}")
        assert len(empty_history.json()["messages"]) == 0

    @pytest.mark.local_credentials
    def test_multiple_users_isolation(self, client):
        """Test that conversations for different users are isolated."""
        user1 = "user_001"
        user2 = "user_002"

        client.post("/chat", json={"user_id": user1, "message": "User 1 message"})
        client.post("/chat", json={"user_id": user2, "message": "User 2 message"})

        history1 = client.get(f"/history/{user1}").json()["messages"]
        history2 = client.get(f"/history/{user2}").json()["messages"]

        assert len(history1) == 2
        assert len(history2) == 2
        assert history1[0]["content"] == "User 1 message"
        assert history2[0]["content"] == "User 2 message"


class TestErrorHandlingFlow:
    """Test error handling across different scenarios."""

    def test_invalid_requests_return_proper_errors(self, client):
        """Test that various invalid requests return appropriate error codes."""
        response = client.post("/chat", json={"user_id": "", "message": "Hello"})
        assert response.status_code == 400

        response = client.post("/chat", json={"user_id": "user", "message": ""})
        assert response.status_code == 400

        response = client.post("/chat", json={"user_id": "", "message": ""})
        assert response.status_code == 400

    def test_history_empty_user_id(self, client):
        """Test history endpoint with empty user_id."""
        response = client.get("/history/")
        assert response.status_code == 404

    def test_clear_nonexistent_conversation(self, client):
        """Test clearing conversation that doesn't exist."""
        response = client.delete("/history/nonexistent_user_999")
        assert response.status_code == 200
        assert response.json()["success"] is False


class TestOAuthFlowIntegration:
    """Test OAuth flow integration."""

    def test_oauth_endpoints_exist(self, client):
        """Test that all OAuth endpoints are accessible."""
        response = client.get("/auth/login?user_id=test_user")
        assert response.status_code in [200, 500]

        response = client.get(
            "/auth/callback?code=fake_code&state=fake_state",
        )
        assert response.status_code in [200, 400, 500]

        response = client.delete("/auth/test_user")
        assert response.status_code in [200, 404, 500]


class TestHealthEndpoints:
    """Test health check and status endpoints."""

    def test_root_endpoint_returns_service_status(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()
        assert "Gemini AI Service" in response.json()["message"]

    def test_health_endpoint_returns_healthy(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestMockClientBehavior:
    """Test the mock client behavior in isolation."""

    def test_mock_client_maintains_state(self):
        """Test that mock client properly maintains conversation state."""
        _reset_mock_client()
        mock = _get_mock_client()

        response1 = mock.send_message("user1", "First message")
        assert "Mock response to: First message" in response1

        response2 = mock.send_message("user1", "Second message")
        assert "Mock response to: Second message" in response2

        history = mock.get_conversation_history("user1")
        assert len(history) == 4
        assert history[0].role == "user"
        assert history[0].content == "First message"
        assert history[1].role == "assistant"
        assert history[2].content == "Second message"

    def test_mock_client_multiple_users(self):
        """Test mock client handles multiple users correctly."""
        _reset_mock_client()
        mock = _get_mock_client()

        mock.send_message("user1", "User 1 msg")
        mock.send_message("user2", "User 2 msg")
        mock.send_message("user1", "User 1 second")

        hist1 = mock.get_conversation_history("user1")
        hist2 = mock.get_conversation_history("user2")

        assert len(hist1) == 4
        assert len(hist2) == 2

    def test_mock_client_clear_specific_user(self):
        """Test that clearing one user's history doesn't affect others."""
        _reset_mock_client()
        mock = _get_mock_client()

        mock.send_message("user1", "Message 1")
        mock.send_message("user2", "Message 2")

        mock.clear_conversation("user1")

        assert len(mock.get_conversation_history("user1")) == 0
        assert len(mock.get_conversation_history("user2")) == 2

    def test_mock_client_validation_errors(self):
        """Test that mock client properly validates inputs."""
        _reset_mock_client()
        mock = _get_mock_client()

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            mock.send_message("", "message")

        with pytest.raises(ValueError, match="message cannot be empty"):
            mock.send_message("user", "")

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            mock.get_conversation_history("")

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            mock.clear_conversation("")


class TestAPIResponseStructure:
    """Test that API responses follow correct structure."""

    @pytest.mark.local_credentials
    def test_send_message_response_structure(self, client):
        """Test send message response has correct structure."""
        response = client.post(
            "/chat",
            json={"user_id": "test", "message": "Hello"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)

    def test_history_response_structure(self, client):
        """Test history response has correct structure."""
        client.post("/chat", json={"user_id": "test", "message": "Test"})
        response = client.get("/history/test")

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "messages" in data
        assert isinstance(data["messages"], list)

        if len(data["messages"]) > 0:
            msg = data["messages"][0]
            assert "role" in msg
            assert "content" in msg

    def test_clear_response_structure(self, client):
        """Test clear conversation response structure."""
        response = client.delete("/history/test_user")

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "success" in data
        assert isinstance(data["success"], bool)


class TestConcurrentRequests:
    """Test handling of concurrent-like scenarios."""

    @pytest.mark.local_credentials
    def test_sequential_requests_same_user(self, client):
        """Test multiple sequential requests for same user work correctly."""
        user_id = "concurrent_user"

        for i in range(5):
            response = client.post(
                "/chat",
                json={"user_id": user_id, "message": f"Message {i}"},
            )
            assert response.status_code == 200

        history = client.get(f"/history/{user_id}").json()
        assert len(history["messages"]) == 10

    @pytest.mark.local_credentials
    def test_interleaved_requests_multiple_users(self, client):
        """Test interleaved requests for multiple users."""
        users = ["user_a", "user_b", "user_c"]

        for i in range(3):
            for user in users:
                client.post(
                    "/chat",
                    json={"user_id": user, "message": f"Msg {i}"},
                )

        for user in users:
            history = client.get(f"/history/{user}").json()
            assert len(history["messages"]) == 6


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_message(self, client):
        """Test handling of very long messages."""
        long_message = "A" * 10000
        response = client.post(
            "/chat",
            json={"user_id": "test", "message": long_message},
        )
        assert response.status_code == 200

    @pytest.mark.local_credentials
    def test_special_characters_in_message(self, client):
        """Test messages with special characters."""
        special_msg = "Hello! @#$%^&*() <script>alert('xss')</script> 你好 🚀"
        response = client.post(
            "/chat",
            json={"user_id": "test", "message": special_msg},
        )
        assert response.status_code == 200
        assert special_msg in client.get("/history/test").json()["messages"][0]["content"]

    def test_unicode_user_id(self, client):
        """Test user IDs with unicode characters."""
        user_id = "user_测试_🎯"
        response = client.post(
            "/chat",
            json={"user_id": user_id, "message": "Test"},
        )
        assert response.status_code == 200

        history = client.get(f"/history/{user_id}")
        assert history.status_code == 200
        assert history.json()["user_id"] == user_id
