"""Tests for the Gemini client implementation."""

import sqlite3
import tempfile
from pathlib import Path

import pytest
from gemini_impl.client import GeminiClient


class TestGeminiClientInit:
    """Test GeminiClient initialization."""

    def test_init_with_valid_api_key(self) -> None:
        """Test initializing with a valid API key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            client = GeminiClient(api_key="test-key", db_path=db_path)
            assert client.api_key == "test-key"
            assert client.db_path == db_path

    def test_init_with_empty_api_key(self) -> None:
        """Test that empty API key raises ValueError."""
        with pytest.raises(ValueError, match="api_key cannot be empty"):
            GeminiClient(api_key="")

    def test_init_creates_database(self) -> None:
        """Test that initialization creates the SQLite database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            GeminiClient(api_key="test-key", db_path=db_path)
            assert Path(db_path).exists()

    def test_init_creates_conversations_table(self) -> None:
        """Test that initialization creates the conversations table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            GeminiClient(api_key="test-key", db_path=db_path)

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'",
                )
                result = cursor.fetchone()
                assert result is not None


class TestGeminiClientSendMessage:
    """Test send_message method."""

    @pytest.fixture
    def client(self) -> GeminiClient:
        """Provide a Gemini client for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            yield GeminiClient(api_key="test-key", db_path=db_path)

    @pytest.mark.local_credentials
    def test_send_message_success(self, client: GeminiClient) -> None:
        """Test sending a message successfully."""
        response = client.send_message("user123", "Hello")
        assert response == "Response to: Hello"

    def test_send_message_empty_user_id(self, client: GeminiClient) -> None:
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            client.send_message("", "Hello")

    def test_send_message_empty_message(self, client: GeminiClient) -> None:
        """Test that empty message raises ValueError."""
        with pytest.raises(ValueError, match="message cannot be empty"):
            client.send_message("user123", "")

    @pytest.mark.local_credentials
    def test_send_message_stores_in_db(self, client: GeminiClient) -> None:
        """Test that sent message is stored in database."""
        client.send_message("user123", "Hello")

        history = client.get_conversation_history("user123")
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[1].role == "assistant"


class TestGeminiClientGetHistory:
    """Test get_conversation_history method."""

    @pytest.fixture
    def client(self) -> GeminiClient:
        """Provide a Gemini client for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            yield GeminiClient(api_key="test-key", db_path=db_path)

    def test_get_history_empty_user(self, client: GeminiClient) -> None:
        """Test getting history for a user with no messages."""
        history = client.get_conversation_history("newuser")
        assert history == []

    @pytest.mark.local_credentials
    def test_get_history_with_messages(self, client: GeminiClient) -> None:
        """Test getting history for a user with messages."""
        client.send_message("user123", "Hello")
        client.send_message("user123", "How are you?")

        history = client.get_conversation_history("user123")
        assert len(history) == 4
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[1].role == "assistant"
        assert history[2].role == "user"
        assert history[2].content == "How are you?"
        assert history[3].role == "assistant"

    def test_get_history_empty_user_id(self, client: GeminiClient) -> None:
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            client.get_conversation_history("")

    @pytest.mark.local_credentials
    def test_get_history_isolated_per_user(self, client: GeminiClient) -> None:
        """Test that history is isolated per user."""
        client.send_message("user1", "Message 1")
        client.send_message("user2", "Message 2")

        history1 = client.get_conversation_history("user1")
        history2 = client.get_conversation_history("user2")

        assert len(history1) == 2
        assert len(history2) == 2
        assert history1[0].content == "Message 1"
        assert history2[0].content == "Message 2"


class TestGeminiClientClearConversation:
    """Test clear_conversation method."""

    @pytest.fixture
    def client(self) -> GeminiClient:
        """Provide a Gemini client for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")
            yield GeminiClient(api_key="test-key", db_path=db_path)

    @pytest.mark.local_credentials
    def test_clear_conversation_success(self, client: GeminiClient) -> None:
        """Test clearing conversation history."""
        client.send_message("user123", "Hello")
        assert len(client.get_conversation_history("user123")) == 2

        result = client.clear_conversation("user123")
        assert result is True
        assert len(client.get_conversation_history("user123")) == 0

    def test_clear_conversation_nonexistent_user(self, client: GeminiClient) -> None:
        """Test clearing conversation for user with no history."""
        result = client.clear_conversation("nonexistent")
        assert result is False

    def test_clear_conversation_empty_user_id(self, client: GeminiClient) -> None:
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            client.clear_conversation("")

    @pytest.mark.local_credentials
    def test_clear_does_not_affect_other_users(self, client: GeminiClient) -> None:
        """Test that clearing one user's conversation doesn't affect others."""
        client.send_message("user1", "Message 1")
        client.send_message("user2", "Message 2")

        client.clear_conversation("user1")

        history1 = client.get_conversation_history("user1")
        history2 = client.get_conversation_history("user2")

        assert len(history1) == 0
        assert len(history2) == 2
