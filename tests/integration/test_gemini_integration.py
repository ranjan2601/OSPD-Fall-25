"""Integration tests for Gemini AI Chat Service.

Tests component interactions with mocked dependencies to verify:
- Interface contracts
- Message handling
- Conversation history
- Multi-user isolation
- Database persistence
- Error handling
"""

import os
import sqlite3
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from gemini_api import AIClient, Message
from gemini_impl.client import GeminiClient
from gemini_impl.oauth import OAuthManager

# Mark all tests in this file as integration tests and for CI/CD
pytestmark = [pytest.mark.integration, pytest.mark.circleci]


@pytest.fixture
def unique_user_id() -> str:
    """Generate unique user_id for test isolation."""
    return f"test_user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def temp_db() -> str:
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def mock_gemini_api_key() -> str:
    """Provide a mock API key for testing."""
    return "test_api_key_" + uuid.uuid4().hex[:16]


class TestGeminiClientInterfaceContract:
    """Test that GeminiClient properly implements AIClient interface."""

    def test_gemini_client_implements_ai_client(self, temp_db, mock_gemini_api_key) -> None:
        """Verify GeminiClient implements AIClient interface."""
        with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel"):
            client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)
            assert isinstance(client, AIClient)

    def test_gemini_client_has_required_methods(self, temp_db, mock_gemini_api_key) -> None:
        """Verify all required methods exist."""
        with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel"):
            client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)
            assert hasattr(client, "send_message")
            assert hasattr(client, "get_conversation_history")
            assert hasattr(client, "clear_conversation")

    def test_gemini_client_method_signatures(self, temp_db, mock_gemini_api_key) -> None:
        """Check method signatures match interface."""
        import inspect

        with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel"):
            client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

            # Check send_message signature
            sig = inspect.signature(client.send_message)
            assert "user_id" in sig.parameters
            assert "message" in sig.parameters

            # Check get_conversation_history signature
            sig = inspect.signature(client.get_conversation_history)
            assert "user_id" in sig.parameters

            # Check clear_conversation signature
            sig = inspect.signature(client.clear_conversation)
            assert "user_id" in sig.parameters


class TestGeminiClientMessageHandling:
    """Test message sending and handling with mocked Gemini API."""

    def test_send_message_with_mocked_api(
        self,
        temp_db,
        mock_gemini_api_key,
        unique_user_id,
    ) -> None:
        """Send message to mocked Gemini API and verify response structure."""
        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "This is a mocked AI response"
            mock_model.generate_content.return_value = mock_response

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)
                response = client.send_message(unique_user_id, "Hello AI")

                assert response == "This is a mocked AI response"
                mock_model.generate_content.assert_called_once_with("Hello AI")

    def test_message_storage_in_database(
        self,
        temp_db,
        mock_gemini_api_key,
        unique_user_id,
    ) -> None:
        """Verify messages are stored correctly in database."""
        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "AI response"
            mock_model.generate_content.return_value = mock_response

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)
                client.send_message(unique_user_id, "Test message")

                # Verify database storage
                with sqlite3.connect(temp_db) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT user_id, role, content FROM conversations WHERE user_id = ?",
                        (unique_user_id,),
                    )
                    rows = cursor.fetchall()

                assert len(rows) == 2  # user message + assistant message
                assert rows[0][1] == "user"
                assert rows[0][2] == "Test message"
                assert rows[1][1] == "assistant"
                assert rows[1][2] == "AI response"

    def test_response_structure_validation(
        self,
        temp_db,
        mock_gemini_api_key,
        unique_user_id,
    ) -> None:
        """Validate the response structure from send_message."""
        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Test response"
            mock_model.generate_content.return_value = mock_response

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)
                response = client.send_message(unique_user_id, "Hello")

                assert isinstance(response, str)
                assert len(response) > 0


class TestGeminiClientConversationHistory:
    """Test conversation history storage and retrieval."""

    def test_retrieve_conversation_history(
        self,
        temp_db,
        mock_gemini_api_key,
        unique_user_id,
    ) -> None:
        """Store multiple messages and retrieve conversation history."""
        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = [
                MagicMock(text="Response 1"),
                MagicMock(text="Response 2"),
                MagicMock(text="Response 3"),
            ]

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

                # Send multiple messages
                client.send_message(unique_user_id, "Message 1")
                client.send_message(unique_user_id, "Message 2")
                client.send_message(unique_user_id, "Message 3")

                # Retrieve history
                history = client.get_conversation_history(unique_user_id)

                assert len(history) == 6  # 3 user + 3 assistant messages
                assert all(isinstance(msg, Message) for msg in history)

    def test_message_order_preservation(
        self,
        temp_db,
        mock_gemini_api_key,
        unique_user_id,
    ) -> None:
        """Verify message order is preserved in conversation history."""
        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = [
                MagicMock(text="Response A"),
                MagicMock(text="Response B"),
            ]

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

                client.send_message(unique_user_id, "First message")
                client.send_message(unique_user_id, "Second message")

                history = client.get_conversation_history(unique_user_id)

                assert history[0].role == "user"
                assert history[0].content == "First message"
                assert history[1].role == "assistant"
                assert history[1].content == "Response A"
                assert history[2].role == "user"
                assert history[2].content == "Second message"
                assert history[3].role == "assistant"
                assert history[3].content == "Response B"

    def test_history_content_validation(
        self,
        temp_db,
        mock_gemini_api_key,
        unique_user_id,
    ) -> None:
        """Verify conversation history content is accurate."""
        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "AI says hello"
            mock_model.generate_content.return_value = mock_response

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

                client.send_message(unique_user_id, "Hello AI")
                history = client.get_conversation_history(unique_user_id)

                assert history[0].content == "Hello AI"
                assert history[1].content == "AI says hello"


class TestGeminiClientClearConversation:
    """Test conversation clearing functionality."""

    def test_clear_conversation_for_user(
        self,
        temp_db,
        mock_gemini_api_key,
        unique_user_id,
    ) -> None:
        """Clear conversation for user and verify history is empty."""
        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Response"
            mock_model.generate_content.return_value = mock_response

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

                # Send messages
                client.send_message(unique_user_id, "Message 1")
                client.send_message(unique_user_id, "Message 2")

                # Clear conversation
                result = client.clear_conversation(unique_user_id)
                assert result is True

                # Verify history is empty
                history = client.get_conversation_history(unique_user_id)
                assert len(history) == 0

    def test_clear_does_not_affect_other_users(self, temp_db, mock_gemini_api_key) -> None:
        """Ensure clearing one user's conversation doesn't affect others."""
        user1 = f"user1_{uuid.uuid4().hex[:8]}"
        user2 = f"user2_{uuid.uuid4().hex[:8]}"

        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_model.generate_content.return_value = MagicMock(text="Response")

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

                # Send messages for both users
                client.send_message(user1, "User 1 message")
                client.send_message(user2, "User 2 message")

                # Clear user1's conversation
                client.clear_conversation(user1)

                # Verify user1's history is empty
                assert len(client.get_conversation_history(user1)) == 0

                # Verify user2's history is intact
                user2_history = client.get_conversation_history(user2)
                assert len(user2_history) == 2
                assert user2_history[0].content == "User 2 message"


class TestGeminiClientMultiUserIsolation:
    """Test multi-user data isolation."""

    def test_multiple_users_separate_histories(self, temp_db, mock_gemini_api_key) -> None:
        """Create conversations for multiple users and verify isolation."""
        users = [f"user_{i}_{uuid.uuid4().hex[:4]}" for i in range(3)]

        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_model.generate_content.return_value = MagicMock(text="Response")

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

                # Send different messages for each user
                for i, user in enumerate(users):
                    client.send_message(user, f"Message from user {i}")

                # Verify each user has their own isolated history
                for i, user in enumerate(users):
                    history = client.get_conversation_history(user)
                    assert len(history) == 2
                    assert history[0].content == f"Message from user {i}"

    def test_concurrent_user_data_isolation(self, temp_db, mock_gemini_api_key) -> None:
        """Verify data isolation with concurrent user access."""
        user1 = f"concurrent_user1_{uuid.uuid4().hex[:8]}"
        user2 = f"concurrent_user2_{uuid.uuid4().hex[:8]}"

        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_model.generate_content.return_value = MagicMock(text="Response")

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

                # Interleave messages from both users
                client.send_message(user1, "User1 Msg1")
                client.send_message(user2, "User2 Msg1")
                client.send_message(user1, "User1 Msg2")
                client.send_message(user2, "User2 Msg2")

                # Verify isolation
                history1 = client.get_conversation_history(user1)
                history2 = client.get_conversation_history(user2)

                assert len(history1) == 4
                assert len(history2) == 4
                assert history1[0].content == "User1 Msg1"
                assert history2[0].content == "User2 Msg1"


class TestGeminiDatabasePersistence:
    """Test database persistence and data survival."""

    def test_data_survives_client_restart(self, temp_db, mock_gemini_api_key, unique_user_id) -> None:
        """Verify data persists across client instances."""
        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_model.generate_content.return_value = MagicMock(text="Response")

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                # First client instance
                client1 = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)
                client1.send_message(unique_user_id, "Persistent message")

                # Second client instance (simulating restart)
                client2 = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)
                history = client2.get_conversation_history(unique_user_id)

                assert len(history) == 2
                assert history[0].content == "Persistent message"

    def test_database_schema_integrity(self, temp_db, mock_gemini_api_key) -> None:
        """Verify database schema is correctly initialized."""
        with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel"):
            _ = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

            # Check table exists
            with sqlite3.connect(temp_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'",
                )
                assert cursor.fetchone() is not None

                # Check columns
                cursor.execute("PRAGMA table_info(conversations)")
                columns = {row[1] for row in cursor.fetchall()}
                assert "user_id" in columns
                assert "role" in columns
                assert "content" in columns
                assert "created_at" in columns


class TestGeminiErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_user_id_handling(self, temp_db, mock_gemini_api_key) -> None:
        """Test handling of invalid user_id."""
        with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel"):
            client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

            with pytest.raises(ValueError, match="user_id cannot be empty"):
                client.send_message("", "Message")

            with pytest.raises(ValueError, match="user_id cannot be empty"):
                client.get_conversation_history("")

            with pytest.raises(ValueError, match="user_id cannot be empty"):
                client.clear_conversation("")

    def test_empty_message_handling(self, temp_db, mock_gemini_api_key, unique_user_id) -> None:
        """Test handling of empty messages."""
        with patch("google.generativeai.configure"), patch("google.generativeai.GenerativeModel"):
            client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

            with pytest.raises(ValueError, match="message cannot be empty"):
                client.send_message(unique_user_id, "")

    def test_api_error_handling(self, temp_db, mock_gemini_api_key, unique_user_id) -> None:
        """Test handling of API errors."""
        with patch("google.generativeai.configure"):
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = Exception("API Error")

            with patch("google.generativeai.GenerativeModel", return_value=mock_model):
                client = GeminiClient(api_key=mock_gemini_api_key, db_path=temp_db)

                with pytest.raises(RuntimeError, match="Error calling Gemini API"):
                    client.send_message(unique_user_id, "Test message")


class TestGeminiOAuthIntegration:
    """Test OAuth flow integration."""

    @pytest.fixture
    def temp_credentials_file(self) -> str:
        """Create temporary OAuth credentials file."""
        credentials = {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "redirect_uris": ["http://localhost:8000/auth/callback"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".json",
            delete=False,
        ) as f:
            import json

            json.dump(credentials, f)
            cred_file = f.name

        yield cred_file
        Path(cred_file).unlink(missing_ok=True)

    def test_oauth_manager_initialization(self, temp_credentials_file, temp_db) -> None:
        """Test OAuth manager initialization."""
        oauth_manager = OAuthManager(
            credentials_file=temp_credentials_file,
            db_path=temp_db,
        )
        assert oauth_manager.credentials_file == temp_credentials_file
        assert oauth_manager.db_path == temp_db

    def test_oauth_authorization_url_generation(
        self,
        temp_credentials_file,
        temp_db,
        unique_user_id,
    ) -> None:
        """Test OAuth authorization URL generation."""
        oauth_manager = OAuthManager(
            credentials_file=temp_credentials_file,
            db_path=temp_db,
        )
        auth_url = oauth_manager.get_authorization_url(unique_user_id)

        assert "https://accounts.google.com" in auth_url
        assert "oauth2" in auth_url

    def test_oauth_credential_storage_and_retrieval(
        self,
        temp_credentials_file,
        temp_db,
        unique_user_id,
    ) -> None:
        """Test OAuth credential storage and retrieval."""
        oauth_manager = OAuthManager(
            credentials_file=temp_credentials_file,
            db_path=temp_db,
        )

        # Store credentials
        mock_credentials = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
        }
        oauth_manager._store_credentials(unique_user_id, mock_credentials)

        # Retrieve credentials
        retrieved = oauth_manager._get_stored_credentials(unique_user_id)
        assert retrieved is not None
        assert retrieved["token"] == "test_access_token"
        assert retrieved["refresh_token"] == "test_refresh_token"

    def test_oauth_credential_deletion(
        self,
        temp_credentials_file,
        temp_db,
        unique_user_id,
    ) -> None:
        """Test OAuth credential deletion."""
        oauth_manager = OAuthManager(
            credentials_file=temp_credentials_file,
            db_path=temp_db,
        )

        # Store then delete
        mock_credentials = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        oauth_manager._store_credentials(unique_user_id, mock_credentials)

        result = oauth_manager.revoke_credentials(unique_user_id)
        assert result is True

        # Verify deleted
        retrieved = oauth_manager._get_stored_credentials(unique_user_id)
        assert retrieved is None
