"""End-to-end tests for Gemini AI Chat Service.

Full workflow tests with real Gemini API to verify:
- Complete chat workflows
- Conversation history persistence
- Multi-user scenarios
- OAuth flows
- Concurrent access
- Special character handling
- Error recovery
- Service health
"""

import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
import pytest

# Mark all tests in this file as e2e tests
pytestmark = pytest.mark.e2e

# Service configuration
SERVICE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30.0


@pytest.fixture(scope="module")
def check_service_running():
    """Verify Gemini service is running on localhost:8000."""
    try:
        response = httpx.get(SERVICE_URL, timeout=2.0)
        if response.status_code != 200:
            pytest.skip(f"Service at {SERVICE_URL} is not responding correctly")
    except (httpx.ConnectError, httpx.TimeoutException):
        pytest.skip(
            f"Service not running at {SERVICE_URL}. Start with: uv run uvicorn gemini_service.main:app --reload",
        )


@pytest.fixture(scope="module")
def check_gemini_api_key():
    """Verify GEMINI_API_KEY environment variable is set."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip(
            "GEMINI_API_KEY not set in environment. Set it with: export GEMINI_API_KEY=your_api_key",
        )
    return api_key


@pytest.fixture
def unique_user_id():
    """Generate unique user_id for test isolation."""
    return f"e2e_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def http_client():
    """Create httpx client for API calls."""
    return httpx.Client(base_url=SERVICE_URL, timeout=TIMEOUT)


class TestGeminiCompleteChatWorkflow:
    """Test complete chat workflow with real Gemini API."""

    def test_gemini_complete_chat_workflow(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Test complete workflow: send message, receive AI response, verify storage."""
        # Send message to AI
        response = http_client.post(
            "/chat",
            json={"user_id": unique_user_id, "message": "Hello! What is 2+2?"},
            params={"authenticated_user_id": unique_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        ai_response = data["response"]

        # Verify response is meaningful (not mock)
        assert len(ai_response) > 0
        assert "Mock response" not in ai_response  # Ensure not using mock client

        # Verify message was stored in database by retrieving history
        history_response = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id})
        assert history_response.status_code == 200
        history_data = history_response.json()

        assert "messages" in history_data
        messages = history_data["messages"]
        assert len(messages) == 2  # user message + assistant response

        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello! What is 2+2?"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == ai_response

    def test_ai_response_quality(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Verify AI responses are meaningful and context-aware."""
        # Send a specific question
        response = http_client.post(
            "/chat",
            json={
                "user_id": unique_user_id,
                "message": "What is the capital of France?",
            },
            params={"authenticated_user_id": unique_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        ai_response = data["response"].lower()

        # Verify response mentions Paris (the correct answer)
        assert "paris" in ai_response


class TestGeminiConversationHistoryPersistence:
    """Test conversation history persistence across multiple messages."""

    def test_conversation_history_persistence(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Send 5 messages and verify all are stored correctly."""
        messages_to_send = [
            "Hello!",
            "What is Python?",
            "Tell me about AI",
            "What is machine learning?",
            "Thank you!",
        ]

        # Send all messages
        for msg in messages_to_send:
            response = http_client.post(
                "/chat",
                json={"user_id": unique_user_id, "message": msg},
                params={"authenticated_user_id": unique_user_id},
            )
            assert response.status_code == 200

        # Retrieve history
        history_response = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id})
        assert history_response.status_code == 200
        history_data = history_response.json()

        messages = history_data["messages"]
        assert len(messages) == 10  # 5 user + 5 assistant messages

        # Verify message order
        for i, sent_msg in enumerate(messages_to_send):
            user_msg_index = i * 2
            assert messages[user_msg_index]["role"] == "user"
            assert messages[user_msg_index]["content"] == sent_msg
            assert messages[user_msg_index + 1]["role"] == "assistant"

    def test_history_retrieval_accuracy(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Verify retrieved history matches sent messages exactly."""
        test_message = f"Unique test message {uuid.uuid4().hex[:8]}"

        # Send message
        send_response = http_client.post(
            "/chat",
            json={"user_id": unique_user_id, "message": test_message},
            params={"authenticated_user_id": unique_user_id},
        )
        assert send_response.status_code == 200
        ai_response = send_response.json()["response"]

        # Retrieve and verify
        history_response = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id})
        messages = history_response.json()["messages"]

        assert messages[0]["content"] == test_message
        assert messages[1]["content"] == ai_response


class TestGeminiMultipleUsersConversation:
    """Test multiple users with separate conversation histories."""

    def test_multiple_users_conversation(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
    ):
        """Verify each user's history is separate with no cross-user data leakage."""
        user_a = f"e2e_userA_{uuid.uuid4().hex[:8]}"
        user_b = f"e2e_userB_{uuid.uuid4().hex[:8]}"

        # User A sends 3 messages
        for i in range(3):
            response = http_client.post(
                "/chat",
                json={"user_id": user_a, "message": f"User A message {i}"},
                params={"authenticated_user_id": user_a},
            )
            assert response.status_code == 200

        # User B sends 2 messages
        for i in range(2):
            response = http_client.post(
                "/chat",
                json={"user_id": user_b, "message": f"User B message {i}"},
                params={"authenticated_user_id": user_b},
            )
            assert response.status_code == 200

        # Verify User A's history
        history_a = http_client.get(f"/history/{user_a}", params={"authenticated_user_id": user_a}).json()["messages"]
        assert len(history_a) == 6  # 3 user + 3 assistant
        assert all("User A" in msg["content"] for msg in history_a if msg["role"] == "user")

        # Verify User B's history
        history_b = http_client.get(f"/history/{user_b}", params={"authenticated_user_id": user_b}).json()["messages"]
        assert len(history_b) == 4  # 2 user + 2 assistant
        assert all("User B" in msg["content"] for msg in history_b if msg["role"] == "user")

        # Verify no cross-contamination
        assert not any("User B" in msg["content"] for msg in history_a if msg["role"] == "user")
        assert not any("User A" in msg["content"] for msg in history_b if msg["role"] == "user")

    def test_user_isolation_stress_test(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
    ):
        """Test isolation with multiple users sending messages simultaneously."""
        users = [f"stress_user_{i}_{uuid.uuid4().hex[:4]}" for i in range(5)]

        # Send unique message for each user
        for user in users:
            response = http_client.post(
                "/chat",
                json={"user_id": user, "message": f"Unique message for {user}"},
                params={"authenticated_user_id": user},
            )
            assert response.status_code == 200

        # Verify each user has exactly their own message
        for user in users:
            history = http_client.get(f"/history/{user}", params={"authenticated_user_id": user}).json()["messages"]
            user_messages = [msg for msg in history if msg["role"] == "user"]
            assert len(user_messages) == 1
            assert f"Unique message for {user}" in user_messages[0]["content"]


class TestGeminiClearHistoryWorkflow:
    """Test clearing conversation history."""

    def test_clear_history_workflow(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Send messages, clear history, and verify it's empty."""
        # Send messages
        for i in range(3):
            response = http_client.post(
                "/chat",
                json={"user_id": unique_user_id, "message": f"Message {i}"},
            )
            assert response.status_code == 200

        # Verify history exists
        history = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id}).json()[
            "messages"
        ]
        assert len(history) > 0

        # Clear history
        clear_response = http_client.delete(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id})
        assert clear_response.status_code == 200
        clear_data = clear_response.json()
        assert clear_data["success"] is True

        # Verify history is empty
        new_history = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id}).json()[
            "messages"
        ]
        assert len(new_history) == 0

    def test_clear_only_affects_target_user(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
    ):
        """Verify clearing one user doesn't affect another user."""
        user1 = f"clear_test1_{uuid.uuid4().hex[:8]}"
        user2 = f"clear_test2_{uuid.uuid4().hex[:8]}"

        # Both users send messages
        http_client.post(
            "/chat",
            json={"user_id": user1, "message": "User 1 message"},
            params={"authenticated_user_id": user1},
        )
        http_client.post(
            "/chat",
            json={"user_id": user2, "message": "User 2 message"},
            params={"authenticated_user_id": user2},
        )

        # Clear user1's history
        http_client.delete(f"/history/{user1}", params={"authenticated_user_id": user1})

        # Verify user1's history is empty, user2's is not
        history1 = http_client.get(f"/history/{user1}", params={"authenticated_user_id": user1}).json()["messages"]
        history2 = http_client.get(f"/history/{user2}", params={"authenticated_user_id": user2}).json()["messages"]

        assert len(history1) == 0
        assert len(history2) > 0


class TestGeminiConcurrentUsers:
    """Test concurrent user access and race conditions."""

    def test_concurrent_users(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
    ):
        """Simulate 3 concurrent users sending messages."""
        users = [f"concurrent_{i}_{uuid.uuid4().hex[:4]}" for i in range(3)]

        def send_message(user_id):
            """Send a message to the chat service."""
            response = http_client.post(
                "/chat",
                json={"user_id": user_id, "message": f"Message from {user_id}"},
                params={"authenticated_user_id": user_id},
            )
            return response.status_code, user_id

        # Send messages concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_message, user) for user in users]
            results = [future.result() for future in as_completed(futures)]

        # Verify all requests succeeded
        assert all(status == 200 for status, _ in results)

        # Verify data integrity - each user has their message
        for user in users:
            history = http_client.get(f"/history/{user}", params={"authenticated_user_id": user}).json()["messages"]
            user_messages = [msg for msg in history if msg["role"] == "user"]
            assert len(user_messages) == 1
            assert user in user_messages[0]["content"]

    def test_concurrent_writes_no_race_condition(
        self,
        check_service_running,
        check_gemini_api_key,
    ):
        """Test multiple concurrent writes to same user don't cause race conditions."""
        user_id = f"race_test_{uuid.uuid4().hex[:8]}"
        num_messages = 5

        def send_numbered_message(msg_num):
            """Send a numbered message."""
            with httpx.Client(base_url=SERVICE_URL, timeout=TIMEOUT) as client:
                response = client.post(
                    "/chat",
                    json={"user_id": user_id, "message": f"Message number {msg_num}"},
                )
                return response.status_code

        # Send messages concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_numbered_message, i) for i in range(num_messages)]
            results = [future.result() for future in as_completed(futures)]

        # All should succeed
        assert all(status == 200 for status in results)

        # Verify all messages were stored
        with httpx.Client(base_url=SERVICE_URL, timeout=TIMEOUT) as client:
            history = client.get(f"/history/{user_id}").json()["messages"]
            user_messages = [msg for msg in history if msg["role"] == "user"]
            assert len(user_messages) == num_messages


class TestGeminiSpecialCharactersHandling:
    """Test handling of special characters and encoding."""

    def test_special_characters_handling(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Test messages with Unicode, emojis, and special characters."""
        special_messages = [
            "Hello 👋 AI!",
            "Test with émojis 🚀🎉",
            "中文测试",
            "Привет мир",
            "Special chars: @#$%^&*()",
            "Newline\ntest",
            "Quote test: 'single' and \"double\"",
        ]

        for msg in special_messages:
            # Send message
            response = http_client.post(
                "/chat",
                json={"user_id": unique_user_id, "message": msg},
                params={"authenticated_user_id": unique_user_id},
            )
            assert response.status_code == 200

        # Retrieve and verify all special characters preserved
        history = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id}).json()[
            "messages"
        ]
        user_messages = [m for m in history if m["role"] == "user"]

        assert len(user_messages) == len(special_messages)
        for i, expected_msg in enumerate(special_messages):
            assert user_messages[i]["content"] == expected_msg

    def test_database_encoding_handling(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Verify database correctly handles various encodings."""
        emoji_message = "Testing emoji storage: 🎯🔥💯✨🚀"

        # Send and retrieve
        http_client.post(
            "/chat",
            json={"user_id": unique_user_id, "message": emoji_message},
            params={"authenticated_user_id": unique_user_id},
        )
        history = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id}).json()[
            "messages"
        ]

        assert history[0]["content"] == emoji_message


class TestGeminiLongConversationHandling:
    """Test handling of long conversations."""

    def test_long_conversation_handling(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Send 20+ messages and verify history retrieval performs well."""
        num_messages = 25

        # Send messages
        for i in range(num_messages):
            response = http_client.post(
                "/chat",
                json={"user_id": unique_user_id, "message": f"Message number {i}"},
            )
            assert response.status_code == 200

        # Retrieve history
        retrieval_start = time.time()
        history = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id}).json()[
            "messages"
        ]
        retrieval_time = time.time() - retrieval_start

        # Verify all messages present
        assert len(history) == num_messages * 2  # user + assistant messages

        # Verify performance is acceptable (< 5 seconds for retrieval)
        assert retrieval_time < 5.0, f"History retrieval took {retrieval_time}s"

    def test_conversation_message_ordering_at_scale(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Verify message ordering is preserved in long conversations."""
        num_messages = 15

        # Send numbered messages
        for i in range(num_messages):
            http_client.post(
                "/chat",
                json={"user_id": unique_user_id, "message": f"Order test {i}"},
            )

        # Verify order
        history = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id}).json()[
            "messages"
        ]
        user_messages = [msg for msg in history if msg["role"] == "user"]

        for i in range(num_messages):
            assert f"Order test {i}" in user_messages[i]["content"]


class TestGeminiErrorRecovery:
    """Test error handling and recovery."""

    def test_service_stability_after_error(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Verify service remains stable after errors."""
        # Send invalid request (empty message)
        invalid_response = http_client.post(
            "/chat",
            json={"user_id": unique_user_id, "message": ""},
            params={"authenticated_user_id": unique_user_id},
        )
        assert invalid_response.status_code == 400

        # Send valid request - should work
        valid_response = http_client.post(
            "/chat",
            json={"user_id": unique_user_id, "message": "Valid message"},
            params={"authenticated_user_id": unique_user_id},
        )
        assert valid_response.status_code == 200

    def test_graceful_error_handling(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
    ):
        """Test graceful handling of various error conditions."""
        test_user = f"error_test_{uuid.uuid4().hex[:8]}"

        # Empty user_id
        response = http_client.post(
            "/chat",
            json={"user_id": "", "message": "Hello"},
            params={"authenticated_user_id": test_user},
        )
        assert response.status_code == 400
        assert "user_id cannot be empty" in response.json()["detail"]

        # Empty message
        response = http_client.post(
            "/chat",
            json={"user_id": "test_user", "message": ""},
            params={"authenticated_user_id": "test_user"},
        )
        assert response.status_code == 400
        assert "message cannot be empty" in response.json()["detail"]

    def test_next_request_after_error(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Verify next request works correctly after an error."""
        # Trigger error
        http_client.post(
            "/chat",
            json={"user_id": "", "message": "Test"},
            params={"authenticated_user_id": unique_user_id},
        )

        # Next request should work
        response = http_client.post(
            "/chat",
            json={"user_id": unique_user_id, "message": "Recovery test"},
            params={"authenticated_user_id": unique_user_id},
        )
        assert response.status_code == 200
        assert "response" in response.json()


class TestGeminiServiceHealthCheck:
    """Test service health and status endpoints."""

    def test_root_endpoint(self, check_service_running, http_client) -> None:
        """Verify root endpoint is responsive."""
        response = http_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Gemini AI Service" in data["message"]

    def test_health_endpoint(self, check_service_running, http_client) -> None:
        """Verify health check endpoint."""
        response = http_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_service_responsiveness(self, check_service_running, http_client) -> None:
        """Verify service responds quickly to health checks."""
        start_time = time.time()
        response = http_client.get("/health")
        response_time = time.time() - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # Should respond in under 1 second


class TestGeminiAPIResponseStructure:
    """Test API response structure and format."""

    def test_chat_response_structure(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Verify /chat endpoint response structure."""
        response = http_client.post(
            "/chat",
            json={"user_id": unique_user_id, "message": "Test"},
            params={"authenticated_user_id": unique_user_id},
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0

    def test_history_response_structure(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Verify /history endpoint response structure."""
        # Send a message first
        http_client.post(
            "/chat",
            json={"user_id": unique_user_id, "message": "Setup message"},
            params={"authenticated_user_id": unique_user_id},
        )

        # Get history
        response = http_client.get(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id})

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "messages" in data
        assert isinstance(data["messages"], list)

        # Verify message structure
        if len(data["messages"]) > 0:
            msg = data["messages"][0]
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["user", "assistant"]

    def test_clear_response_structure(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
        unique_user_id,
    ):
        """Verify /history delete endpoint response structure."""
        # Send a message first
        http_client.post(
            "/chat",
            json={"user_id": unique_user_id, "message": "To be cleared"},
            params={"authenticated_user_id": unique_user_id},
        )

        # Clear history
        response = http_client.delete(f"/history/{unique_user_id}", params={"authenticated_user_id": unique_user_id})

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "success" in data
        assert isinstance(data["success"], bool)


class TestGeminiPerUserAuthorizationEnforcement:
    """Test per-user API key authorization enforcement."""

    def test_user_cannot_access_other_users_chat(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
    ):
        """Verify User A cannot send chat message as User B."""
        user_a = f"auth_user_a_{uuid.uuid4().hex[:8]}"
        user_b = f"auth_user_b_{uuid.uuid4().hex[:8]}"

        # User A tries to send message as User B (impersonation attempt)
        response = http_client.post(
            "/chat",
            json={"user_id": user_b, "message": "Malicious message"},
            params={"authenticated_user_id": user_a},
        )

        # Should be forbidden - User A cannot act as User B
        assert response.status_code == 403
        assert "Unauthorized" in response.json()["detail"] or "Cannot access" in response.json()["detail"]

    def test_user_cannot_access_other_users_history(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
    ):
        """Verify User A cannot retrieve User B's conversation history."""
        user_a = f"auth_user_a_{uuid.uuid4().hex[:8]}"
        user_b = f"auth_user_b_{uuid.uuid4().hex[:8]}"

        # User A tries to access User B's history
        response = http_client.get(
            f"/history/{user_b}",
            params={"authenticated_user_id": user_a},
        )

        # Should be forbidden
        assert response.status_code == 403
        assert "Unauthorized" in response.json()["detail"] or "Cannot access" in response.json()["detail"]

    def test_user_cannot_delete_other_users_history(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
    ):
        """Verify User A cannot delete User B's conversation history."""
        user_a = f"auth_user_a_{uuid.uuid4().hex[:8]}"
        user_b = f"auth_user_b_{uuid.uuid4().hex[:8]}"

        # User A tries to delete User B's history
        response = http_client.delete(
            f"/history/{user_b}",
            params={"authenticated_user_id": user_a},
        )

        # Should be forbidden
        assert response.status_code == 403
        assert "Unauthorized" in response.json()["detail"] or "Cannot access" in response.json()["detail"]

    def test_user_can_access_own_resources(
        self,
        check_service_running,
        check_gemini_api_key,
        http_client,
    ):
        """Verify user can access their own resources when authenticated_user_id matches."""
        user = f"auth_own_user_{uuid.uuid4().hex[:8]}"

        # Send message to own resource
        response = http_client.post(
            "/chat",
            json={"user_id": user, "message": "My own message"},
            params={"authenticated_user_id": user},
        )

        # Should succeed
        assert response.status_code == 200
        assert "response" in response.json()

        # Verify can retrieve own history
        history_response = http_client.get(
            f"/history/{user}",
            params={"authenticated_user_id": user},
        )

        # Should succeed
        assert history_response.status_code == 200
        assert "messages" in history_response.json()
