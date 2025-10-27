"""Tests for the abstract AI chat client interface."""

import pytest
from gemini_api.client import AIClient, Message


class ConcreteAIClient(AIClient):
    """Concrete implementation of AIClient for testing."""

    def __init__(self) -> None:
        """Initialize with empty conversation storage."""
        self.conversations: dict[str, list[Message]] = {}

    def send_message(self, user_id: str, message: str) -> str:
        """Send a message and return a mock response."""
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        if not message:
            msg = "message cannot be empty"
            raise ValueError(msg)

        if user_id not in self.conversations:
            self.conversations[user_id] = []

        self.conversations[user_id].append(Message(role="user", content=message))
        response = f"Response to: {message}"
        self.conversations[user_id].append(Message(role="assistant", content=response))

        return response

    def get_conversation_history(self, user_id: str) -> list[Message]:
        """Return the conversation history for a user."""
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        return self.conversations.get(user_id, [])

    def clear_conversation(self, user_id: str) -> bool:
        """Clear the conversation history for a user."""
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        if user_id in self.conversations:
            self.conversations[user_id] = []
            return True
        return False


class TestAIClientAbstractMethods:
    """Test that AIClient enforces abstract methods."""

    def test_cannot_instantiate_abstract_client(self) -> None:
        """Test that AIClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIClient()  # type: ignore[abstract]


class TestMessage:
    """Test the Message dataclass."""

    def test_message_creation(self) -> None:
        """Test creating a Message instance."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_message_assistant_role(self) -> None:
        """Test creating an assistant message."""
        msg = Message(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"


class TestConcreteAIClient:
    """Test the concrete implementation of AIClient."""

    @pytest.fixture
    def client(self) -> ConcreteAIClient:
        """Provide a concrete client for testing."""
        return ConcreteAIClient()

    def test_send_message_success(self, client: ConcreteAIClient) -> None:
        """Test sending a message successfully."""
        response = client.send_message("user123", "Hello")
        assert response == "Response to: Hello"

    def test_send_message_empty_user_id(self, client: ConcreteAIClient) -> None:
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            client.send_message("", "Hello")

    def test_send_message_empty_message(self, client: ConcreteAIClient) -> None:
        """Test that empty message raises ValueError."""
        with pytest.raises(ValueError, match="message cannot be empty"):
            client.send_message("user123", "")

    def test_get_conversation_history_new_user(self, client: ConcreteAIClient) -> None:
        """Test getting history for a user with no messages."""
        history = client.get_conversation_history("newuser")
        assert history == []

    def test_get_conversation_history_existing_user(
        self, client: ConcreteAIClient,
    ) -> None:
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

    def test_get_conversation_history_empty_user_id(
        self, client: ConcreteAIClient,
    ) -> None:
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            client.get_conversation_history("")

    def test_clear_conversation_success(self, client: ConcreteAIClient) -> None:
        """Test clearing conversation history."""
        client.send_message("user123", "Hello")
        assert len(client.get_conversation_history("user123")) == 2

        result = client.clear_conversation("user123")
        assert result is True
        assert len(client.get_conversation_history("user123")) == 0

    def test_clear_conversation_nonexistent_user(self, client: ConcreteAIClient) -> None:
        """Test clearing conversation for user with no history."""
        result = client.clear_conversation("nonexistent")
        assert result is False

    def test_clear_conversation_empty_user_id(self, client: ConcreteAIClient) -> None:
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            client.clear_conversation("")
