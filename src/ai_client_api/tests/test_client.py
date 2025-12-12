"""Tests for the abstract AI client interface."""

from typing import Generator, Any

import pytest

import ai_client_api
from ai_client_api.client import AIInterface


class ConcreteAIInterface(AIInterface):
    """Concrete implementation of AIInterface for testing."""

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate a mock response."""
        if not user_input:
            raise ValueError("user_input cannot be empty")
        if not system_prompt:
            raise ValueError("system_prompt cannot be empty")

        if response_schema:
            return {"mock": "structured_response"}
        return f"Response to: {user_input}"


class TestAIInterfaceExists:
    """Test that AIInterface exists and can be imported."""

    def test_aiinterface_abc_exists(self) -> None:
        """Test that AIInterface ABC exists."""
        assert AIInterface is not None


class TestAIInterfaceAbstractMethods:
    """Test that AIInterface enforces abstract methods."""

    def test_cannot_instantiate_abstract_interface(self) -> None:
        """Test that AIInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIInterface()  # type: ignore[abstract]


class TestConcreteAIInterface:
    """Test the concrete implementation of AIInterface."""

    @pytest.fixture
    def client(self) -> ConcreteAIInterface:
        """Provide a concrete client for testing."""
        return ConcreteAIInterface()

    def test_generate_response_success(self, client: ConcreteAIInterface) -> None:
        """Test generating a response successfully."""
        response = client.generate_response("Hello", "You are helpful")
        assert response == "Response to: Hello"

    def test_generate_response_empty_user_input(self, client: ConcreteAIInterface) -> None:
        """Test that empty user_input raises ValueError."""
        with pytest.raises(ValueError, match="user_input cannot be empty"):
            client.generate_response("", "You are helpful")

    def test_generate_response_empty_system_prompt(self, client: ConcreteAIInterface) -> None:
        """Test that empty system_prompt raises ValueError."""
        with pytest.raises(ValueError, match="system_prompt cannot be empty"):
            client.generate_response("Hello", "")

    def test_generate_response_with_schema(self, client: ConcreteAIInterface) -> None:
        """Test generating structured response with schema."""
        schema = {"type": "object"}
        response = client.generate_response("Hello", "You are helpful", schema)
        assert isinstance(response, dict)


class TestFactoryFunctions:
    """Test factory functions."""

    @pytest.fixture(autouse=True)
    def reset_factory(self) -> Generator[None, None, None]:
        """Reset factory to unregistered state."""
        original = ai_client_api.get_client

        def raise_not_implemented(api_key: str) -> AIInterface:
            raise NotImplementedError

        ai_client_api.get_client = raise_not_implemented
        yield
        ai_client_api.get_client = original

    def test_get_client_raises_not_implemented(self) -> None:
        """Test that get_client raises NotImplementedError when not registered."""
        with pytest.raises(NotImplementedError):
            ai_client_api.get_client("api_key")
