"""Unit tests for AIChatOrchestrator."""

from typing import Any
from unittest.mock import Mock


def test_orchestrator_initialization(mock_ai_client: Any, mock_chat_client: Any) -> None:
    """Test orchestrator initialization."""
    from ai_chat_orchestrator import AIChatOrchestrator

    orch = AIChatOrchestrator(
        ai_client=mock_ai_client,
        chat_client=mock_chat_client,
    )

    assert orch.ai_client == mock_ai_client
    assert orch.chat_client == mock_chat_client
    assert "helpful AI assistant" in orch.system_prompt


def test_handle_message_success(orchestrator: Any, mock_ai_client: Any, mock_chat_client: Any) -> None:
    """Test successful message handling."""
    result = orchestrator.handle_message("channel_789", "msg_123")

    assert result is True
    mock_chat_client.get_messages.assert_called_once_with("channel_789", limit=100)
    mock_ai_client.generate_response.assert_called_once()
    call_args = mock_ai_client.generate_response.call_args
    assert call_args[1]["user_input"] == "Hello AI"
    assert call_args[1]["response_schema"] is None
    mock_chat_client.send_message.assert_called_once()


def test_handle_message_empty_content(orchestrator: Any, mock_chat_client: Any) -> None:
    """Test handling empty message content."""
    empty_message = Mock()
    empty_message.id = "msg_123"
    empty_message.content = ""
    mock_chat_client.get_messages.return_value = [empty_message]

    result = orchestrator.handle_message("channel_789", "msg_123")

    assert result is False


def test_handle_message_ai_error(orchestrator: Any, mock_ai_client: Any, mock_chat_client: Any) -> None:
    """Test error handling when AI service fails."""
    mock_ai_client.generate_response.side_effect = RuntimeError("AI service down")

    result = orchestrator.handle_message("channel_789", "msg_123")

    assert result is False
    mock_chat_client.send_message.assert_not_called()


def test_handle_message_chat_send_fails(orchestrator: Any, mock_chat_client: Any) -> None:
    """Test when sending message to chat fails."""
    mock_chat_client.send_message.return_value = False

    result = orchestrator.handle_message("channel_789", "msg_123")

    assert result is False


def test_handle_structured_ai_response(orchestrator: Any, mock_ai_client: Any, mock_chat_client: Any) -> None:
    """Test handling AI response that returns dict."""
    mock_ai_client.generate_response.return_value = {"answer": "42", "confidence": 0.95}

    result = orchestrator.handle_message("channel_789", "msg_123")

    assert result is True
    mock_chat_client.send_message.assert_called_once()
    sent_message = mock_chat_client.send_message.call_args[0][1]
    assert isinstance(sent_message, str)


def test_process_direct(orchestrator: Any, mock_ai_client: Any, mock_chat_client: Any) -> None:
    """Test direct message processing."""
    result = orchestrator.process_direct("channel_789", "What is 2+2?")

    assert result == "Mock AI response"
    mock_chat_client.get_message.assert_not_called()
    mock_ai_client.generate_response.assert_called_once()
    mock_chat_client.send_message.assert_called_once()


def test_process_direct_error(orchestrator: Any, mock_ai_client: Any) -> None:
    """Test direct processing with AI error."""
    mock_ai_client.generate_response.side_effect = RuntimeError("Error")

    result = orchestrator.process_direct("channel_789", "Test")

    assert result is None
