"""Unit tests for orchestrator telemetry functionality."""

import pytest
from unittest.mock import Mock

from ai_chat_orchestrator import AIChatOrchestrator


def test_initial_metrics() -> None:
    """Verify metrics start at zero."""
    mock_ai = Mock()
    mock_chat = Mock()

    orchestrator = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_chat)
    metrics = orchestrator.get_metrics()

    assert metrics["total_requests"] == 0
    assert metrics["successful_requests"] == 0
    assert metrics["failed_requests"] == 0
    assert metrics["success_rate"] == 0.0
    assert metrics["average_latency_seconds"] == 0.0


def test_successful_request_metrics() -> None:
    """Verify successful request increments correct metrics."""
    mock_ai = Mock()
    mock_ai.generate_response.return_value = "AI response"

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Hello"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    orchestrator = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_chat)

    result = orchestrator.handle_message("channel1", "msg1")

    assert result is True
    metrics = orchestrator.get_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["successful_requests"] == 1
    assert metrics["failed_requests"] == 0
    assert metrics["success_rate"] == 1.0
    assert metrics["failure_rate"] == 0.0
    assert metrics["average_latency_seconds"] > 0


def test_failed_request_metrics() -> None:
    """Verify failed request increments failure counter."""
    mock_ai = Mock()
    mock_ai.generate_response.return_value = "AI response"

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Hello"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = False  # Simulate failure

    orchestrator = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_chat)

    result = orchestrator.handle_message("channel1", "msg1")

    assert result is False
    metrics = orchestrator.get_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["successful_requests"] == 0
    assert metrics["failed_requests"] == 1
    assert metrics["success_rate"] == 0.0
    assert metrics["failure_rate"] == 1.0


def test_exception_tracked_as_failure() -> None:
    """Verify exceptions are tracked as failures."""
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = RuntimeError("AI error")

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Hello"
    mock_chat.get_messages.return_value = [mock_message]

    orchestrator = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_chat)

    result = orchestrator.handle_message("channel1", "msg1")

    assert result is False
    metrics = orchestrator.get_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["failed_requests"] == 1


def test_multiple_requests_aggregate_metrics() -> None:
    """Verify metrics aggregate correctly over multiple requests."""
    mock_ai = Mock()
    mock_ai.generate_response.return_value = "AI response"

    mock_chat = Mock()

    # Create different messages for each call
    mock_message1 = Mock()
    mock_message1.id = "msg1"
    mock_message1.content = "Hello"

    mock_message2 = Mock()
    mock_message2.id = "msg2"
    mock_message2.content = "Hello"

    mock_message3 = Mock()
    mock_message3.id = "msg3"
    mock_message3.content = "Hello"

    mock_chat.get_messages.side_effect = [[mock_message1], [mock_message2], [mock_message3]]
    mock_chat.send_message.side_effect = [True, True, False]  # 2 success, 1 failure

    orchestrator = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_chat)

    orchestrator.handle_message("ch1", "msg1")
    orchestrator.handle_message("ch2", "msg2")
    orchestrator.handle_message("ch3", "msg3")

    metrics = orchestrator.get_metrics()
    assert metrics["total_requests"] == 3
    assert metrics["successful_requests"] == 2
    assert metrics["failed_requests"] == 1
    assert metrics["success_rate"] == pytest.approx(2 / 3)
    assert metrics["failure_rate"] == pytest.approx(1 / 3)
    assert metrics["average_latency_seconds"] > 0


def test_process_direct_tracks_metrics() -> None:
    """Verify process_direct method tracks metrics."""
    mock_ai = Mock()
    mock_ai.generate_response.return_value = "AI response"

    mock_chat = Mock()
    mock_chat.send_message.return_value = True

    orchestrator = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_chat)

    result = orchestrator.process_direct("channel1", "Hello AI")

    assert result == "AI response"
    metrics = orchestrator.get_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["successful_requests"] == 1
    assert metrics["average_latency_seconds"] > 0


def test_latency_components_tracked() -> None:
    """Verify AI and chat latency components are tracked separately."""
    mock_ai = Mock()
    mock_ai.generate_response.return_value = "AI response"

    mock_chat = Mock()
    mock_chat.send_message.return_value = True

    orchestrator = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_chat)

    orchestrator.process_direct("channel1", "Test message")

    metrics = orchestrator.get_metrics()
    assert "average_ai_time_seconds" in metrics
    assert "average_chat_time_seconds" in metrics
    assert metrics["average_ai_time_seconds"] >= 0
    assert metrics["average_chat_time_seconds"] >= 0
    assert metrics["average_latency_seconds"] >= metrics["average_ai_time_seconds"]


def test_empty_message_tracked_as_failure() -> None:
    """Verify empty messages are tracked as failures."""
    mock_ai = Mock()
    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = ""  # Empty content
    mock_chat.get_messages.return_value = [mock_message]

    orchestrator = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_chat)

    result = orchestrator.handle_message("channel1", "msg1")

    assert result is False
    metrics = orchestrator.get_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["failed_requests"] == 1
