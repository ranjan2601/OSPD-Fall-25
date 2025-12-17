"""Integration tests for complete Chat -> AI -> Tickets user flow.

These tests verify the full HW3 requirement:
1. User Input (Chat)
2. Routing/Reasoning (AI)
3. Execution (Ticket Service)
4. Response (Chat)
"""

import pytest
from unittest.mock import Mock, patch

from ai_chat_orchestrator import AIChatOrchestrator
from ai_chat_orchestrator.factory import (
    create_gemini_discord_orchestrator,
    create_gemini_slack_orchestrator,
)


@pytest.mark.integration
def test_complete_user_flow_chat_to_ai_to_tickets() -> None:
    """Test complete flow: Chat -> AI -> Tickets -> Chat response."""
    # Setup mocks
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = [
        "GET_TICKETS:limit=3",  # AI decides to fetch tickets
        "Here are your 3 most recent open tickets",  # AI summarizes
    ]

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg123"
    mock_message.content = "Show me my recent tickets"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_t1 = Mock()
    mock_t1.id = "T1"
    mock_t1.title = "Fix login bug"
    mock_t1.status = "open"
    mock_t1.description = "Login bug details"

    mock_t2 = Mock()
    mock_t2.id = "T2"
    mock_t2.title = "Add feature X"
    mock_t2.status = "open"
    mock_t2.description = "Feature X details"

    mock_t3 = Mock()
    mock_t3.id = "T3"
    mock_t3.title = "Update docs"
    mock_t3.status = "open"
    mock_t3.description = "Documentation updates"

    mock_ticket = Mock()
    mock_ticket.search_tickets.return_value = [mock_t1, mock_t2, mock_t3]

    # Create orchestrator with all three components
    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    # Execute user flow
    result = orchestrator.handle_message("channel_456", "msg123")

    # Verify complete flow
    assert result is True
    mock_chat.get_messages.assert_called_once()  # 1. User Input
    assert mock_ai.generate_response.call_count == 2  # 2. AI Reasoning + Summary
    mock_ticket.search_tickets.assert_called_once()  # 3. Ticket Execution
    mock_chat.send_message.assert_called_once()  # 4. Response to Chat


@pytest.mark.integration
def test_user_flow_with_search_tickets() -> None:
    """Test user flow with ticket search by status."""
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = [
        "SEARCH_TICKETS:status=in_progress",
        "You have 2 tickets in progress",
    ]

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "What tickets am I working on?"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_t1 = Mock()
    mock_t1.id = "T1"
    mock_t1.title = "Task 1"
    mock_t1.status = "in_progress"
    mock_t1.description = "Task 1 description"

    mock_t2 = Mock()
    mock_t2.id = "T2"
    mock_t2.title = "Task 2"
    mock_t2.status = "in_progress"
    mock_t2.description = "Task 2 description"

    mock_ticket = Mock()
    mock_ticket.search_tickets.return_value = [mock_t1, mock_t2]

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    result = orchestrator.handle_message("ch1", "msg1")

    assert result is True
    mock_ticket.search_tickets.assert_called_once()


@pytest.mark.integration
def test_user_flow_without_tickets() -> None:
    """Test user flow when user asks non-ticket question."""
    mock_ai = Mock()
    mock_ai.generate_response.return_value = "AI is artificial intelligence"

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "What is AI?"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_ticket = Mock()

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    result = orchestrator.handle_message("ch1", "msg1")

    assert result is True
    # Ticket client should not be called for non-ticket questions
    mock_ticket.list_tickets.assert_not_called()
    mock_ticket.search_tickets.assert_not_called()


@pytest.mark.integration
def test_discord_with_ticket_integration() -> None:
    """Test Discord orchestrator with ticket integration."""
    with patch("ai_chat_orchestrator.factory.ai_client_api.get_client") as mock_ai_get:
        with patch("ai_chat_orchestrator.factory.chat_client_api.get_client") as mock_chat_get:
            mock_ai = Mock()
            mock_ai.generate_response.return_value = "Response"
            mock_ai_get.return_value = mock_ai

            mock_chat = Mock()
            mock_chat_get.return_value = mock_chat

            orchestrator = create_gemini_discord_orchestrator(
                gemini_api_key="test_key"
            )

            # Verify orchestrator was created
            assert orchestrator is not None
            assert orchestrator.ai_client is not None
            assert orchestrator.chat_client is not None


@pytest.mark.integration
def test_slack_with_ticket_integration() -> None:
    """Test Slack orchestrator with ticket integration."""
    with patch("ai_chat_orchestrator.factory.ai_client_api.get_client") as mock_ai_get:
        mock_ai = Mock()
        mock_ai.generate_response.return_value = "Response"
        mock_ai_get.return_value = mock_ai

        orchestrator = create_gemini_slack_orchestrator(
            gemini_api_key="test_key",
            slack_token="xoxb-test",
        )

        # Verify orchestrator was created
        assert orchestrator is not None
        assert orchestrator.ai_client is not None
        assert orchestrator.chat_client is not None


@pytest.mark.integration
def test_error_handling_in_ticket_flow() -> None:
    """Test error handling when ticket service fails."""
    mock_ai = Mock()
    mock_ai.generate_response.return_value = "GET_TICKETS:limit=5"

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Show tickets"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_ticket = Mock()
    mock_ticket.list_tickets.side_effect = RuntimeError("Ticket API down")

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    # Should handle error gracefully
    result = orchestrator.handle_message("ch1", "msg1")

    # Should still return True because a response was sent
    assert result is True
    # User should still get a response (even if it's an error message)
    mock_chat.send_message.assert_called_once()


@pytest.mark.integration
def test_metrics_tracked_during_full_flow() -> None:
    """Test that telemetry is tracked during complete flow."""
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = [
        "GET_TICKETS:limit=2",
        "Here are your tickets",
    ]

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Show tickets"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_t1 = Mock()
    mock_t1.id = "T1"
    mock_t1.title = "Task 1"
    mock_t1.status = "open"
    mock_t1.description = "Task description"

    mock_ticket = Mock()
    mock_ticket.search_tickets.return_value = [mock_t1]

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    # Execute flow
    orchestrator.handle_message("ch1", "msg1")

    # Verify metrics were tracked
    metrics = orchestrator.get_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["successful_requests"] == 1
    assert metrics["average_latency_seconds"] > 0
    assert metrics["average_ai_time_seconds"] > 0


@pytest.mark.integration
def test_process_direct_full_flow() -> None:
    """Test process_direct method with complete ticket flow."""
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = [
        "GET_TICKET:id=PROJ-123",
        "Ticket PROJ-123: Fix critical bug",
    ]

    mock_chat = Mock()
    mock_chat.send_message.return_value = True

    mock_t = Mock()
    mock_t.id = "PROJ-123"
    mock_t.title = "Fix critical bug"
    mock_t.status = "open"
    mock_t.description = "Critical bug in login system"

    mock_ticket = Mock()
    mock_ticket.get_ticket.return_value = mock_t

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    result = orchestrator.process_direct("ch1", "Show me ticket PROJ-123")

    assert result == "Ticket PROJ-123: Fix critical bug"
    mock_ticket.get_ticket.assert_called_once_with("PROJ-123")

