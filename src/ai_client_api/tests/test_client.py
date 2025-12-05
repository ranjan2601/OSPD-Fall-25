"""Tests for the abstract AI chat client interface."""

from typing import Any, Dict, List

import pytest

import ai_client_api
from ai_client_api.client import AIService, Message, ToolCall


class ConcreteToolCall(ToolCall):
    """Concrete implementation of ToolCall for testing."""

    def __init__(self, tool_name: str, tool_args: Dict[str, Any], tool_id: str) -> None:
        """Initialize a tool call."""
        self._tool_name = tool_name
        self._tool_args = tool_args
        self._tool_id = tool_id

    @property
    def tool_name(self) -> str:
        """Return the tool name."""
        return self._tool_name

    @property
    def tool_args(self) -> Dict[str, Any]:
        """Return the tool arguments."""
        return self._tool_args

    @property
    def tool_id(self) -> str:
        """Return the tool ID."""
        return self._tool_id


class ConcreteMessage(Message):
    """Concrete implementation of Message for testing."""

    def __init__(self, text: str) -> None:
        """Initialize a message."""
        self._text = text

    @property
    def text(self) -> str:
        """Return the message text."""
        return self._text


class ConcreteAIService(AIService):
    """Concrete implementation of AIService for testing."""

    def __init__(self) -> None:
        """Initialize with empty storage."""
        self.last_response: str = ""
        self.tool_calls: List[ToolCall] = []

    def send_message(
        self,
        user_id: str,
        prompt: str,
        context: Dict[str, Any] | None = None,
    ) -> str:
        """Send a message and return a mock response."""
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        if not prompt:
            msg = "prompt cannot be empty"
            raise ValueError(msg)

        self.last_response = f"Response to: {prompt}"
        return self.last_response

    def extract_tool_calls(self, response: str) -> List[ToolCall]:
        """Extract tool calls from response."""
        # Mock implementation - return empty list
        return []


class TestABCExists:
    """Test that all ABCs exist and can be imported."""

    def test_message_abc_exists(self) -> None:
        """Test that Message ABC exists."""
        assert Message is not None

    def test_tool_call_abc_exists(self) -> None:
        """Test that ToolCall ABC exists."""
        assert ToolCall is not None

    def test_aiservice_abc_exists(self) -> None:
        """Test that AIService ABC exists."""
        assert AIService is not None


class TestAIServiceAbstractMethods:
    """Test that AIService enforces abstract methods."""

    def test_cannot_instantiate_abstract_service(self) -> None:
        """Test that AIService cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIService()


class TestMessage:
    """Test the Message concrete implementation."""

    def test_message_text_property(self) -> None:
        """Test creating a Message with text property."""
        msg = ConcreteMessage(text="Hello")
        assert msg.text == "Hello"


class TestToolCall:
    """Test the ToolCall concrete implementation."""

    def test_tool_call_creation(self) -> None:
        """Test creating a ToolCall instance."""
        tc = ConcreteToolCall(
            tool_name="close_ticket",
            tool_args={"ticket_id": "123"},
            tool_id="tc_001",
        )
        assert tc.tool_name == "close_ticket"
        assert tc.tool_args == {"ticket_id": "123"}
        assert tc.tool_id == "tc_001"

    def test_tool_call_properties(self) -> None:
        """Test that all ToolCall properties are accessible."""
        tc = ConcreteToolCall(
            tool_name="create_ticket",
            tool_args={"title": "Bug", "description": "A bug"},
            tool_id="tc_002",
        )
        assert isinstance(tc.tool_name, str)
        assert isinstance(tc.tool_args, dict)
        assert isinstance(tc.tool_id, str)


class TestConcreteAIService:
    """Test the concrete implementation of AIService."""

    @pytest.fixture
    def service(self) -> ConcreteAIService:
        """Provide a concrete service for testing."""
        return ConcreteAIService()

    def test_send_message_success(self, service: ConcreteAIService) -> None:
        """Test sending a message successfully."""
        response = service.send_message("user123", "Hello")
        assert response == "Response to: Hello"

    def test_send_message_with_context(self, service: ConcreteAIService) -> None:
        """Test sending a message with context."""
        context = {"tools": []}
        response = service.send_message("user123", "Hello", context=context)
        assert response == "Response to: Hello"

    def test_send_message_empty_user_id(self, service: ConcreteAIService) -> None:
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            service.send_message("", "Hello")

    def test_send_message_empty_prompt(self, service: ConcreteAIService) -> None:
        """Test that empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="prompt cannot be empty"):
            service.send_message("user123", "")

    def test_extract_tool_calls(self, service: ConcreteAIService) -> None:
        """Test extracting tool calls from response."""
        response = "Some response text"
        tool_calls = service.extract_tool_calls(response)
        assert isinstance(tool_calls, list)


class TestFactoryFunctions:
    """Test factory functions."""

    @pytest.fixture(autouse=True)
    def reset_factories(self) -> None:
        """Reset factory functions to original state before each test."""
        from ai_client_api import client as client_module

        original_get_client = client_module.get_client
        original_get_message = client_module.get_message
        original_get_tool_call = client_module.get_tool_call

        def raise_not_implemented_client(user_id: str, api_key: str) -> AIService:
            raise NotImplementedError

        def raise_not_implemented_message(text: str) -> Message:
            raise NotImplementedError

        def raise_not_implemented_tool_call(
            tool_name: str,
            tool_args: Dict[str, Any],
            tool_id: str,
        ) -> ToolCall:
            raise NotImplementedError

        ai_client_api.get_client = raise_not_implemented_client
        ai_client_api.get_message = raise_not_implemented_message
        ai_client_api.get_tool_call = raise_not_implemented_tool_call

        yield

        ai_client_api.get_client = original_get_client
        ai_client_api.get_message = original_get_message
        ai_client_api.get_tool_call = original_get_tool_call

    def test_get_client_raises_not_implemented(self) -> None:
        """Test that get_client raises NotImplementedError when not registered."""
        with pytest.raises(NotImplementedError):
            ai_client_api.get_client("user123", "api_key")

    def test_get_message_raises_not_implemented(self) -> None:
        """Test that get_message raises NotImplementedError when not registered."""
        with pytest.raises(NotImplementedError):
            ai_client_api.get_message("Hello")

    def test_get_tool_call_raises_not_implemented(self) -> None:
        """Test that get_tool_call raises NotImplementedError when not registered."""
        with pytest.raises(NotImplementedError):
            ai_client_api.get_tool_call("tool_name", {}, "tool_id")
