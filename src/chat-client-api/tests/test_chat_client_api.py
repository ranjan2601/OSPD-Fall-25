"""Unit tests for chat client API contract."""

import pytest

import chat_client_api


def test_api_exports_client() -> None:
    """Test that the API exports the ChatInterface class."""
    assert hasattr(chat_client_api, "ChatInterface")
    assert chat_client_api.ChatInterface is not None


def test_api_exports_chat_message() -> None:
    """Test that the API exports the Message class."""
    assert hasattr(chat_client_api, "Message")
    assert chat_client_api.Message is not None


def test_client_is_abstract() -> None:
    """Test that ChatInterface cannot be instantiated directly."""
    with pytest.raises(TypeError):
        chat_client_api.ChatInterface()  # type: ignore[abstract]


def test_chat_message_is_abstract() -> None:
    """Test that Message cannot be instantiated directly."""
    with pytest.raises(TypeError):
        chat_client_api.Message()  # type: ignore[abstract]


def test_chat_interface_has_required_methods() -> None:
    """Test that ChatInterface has the required standardized methods."""
    assert hasattr(chat_client_api.ChatInterface, "send_message")
    assert hasattr(chat_client_api.ChatInterface, "get_messages")
    assert hasattr(chat_client_api.ChatInterface, "delete_message")


def test_message_has_required_properties() -> None:
    """Test that Message has the required standardized properties."""
    assert hasattr(chat_client_api.Message, "id")
    assert hasattr(chat_client_api.Message, "content")
    assert hasattr(chat_client_api.Message, "sender_id")
