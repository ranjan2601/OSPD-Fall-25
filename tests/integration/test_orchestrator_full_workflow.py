"""Integration tests for complete orchestrator workflows.

Tests the full Input -> AI -> Tickets -> Output workflow with proper
component interactions and error handling.
"""

import pytest
from unittest.mock import Mock, patch
from tickets_api import TicketStatus


@pytest.mark.integration
def test_complete_chat_to_tickets_workflow() -> None:
    """Test complete workflow: Chat message -> AI interpretation -> Ticket fetch -> Chat response."""
    from ai_chat_orchestrator import AIChatOrchestrator

    # Setup all components
    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    # Setup chat message
    mock_message = Mock()
    mock_message.id = "msg_123"
    mock_message.content = "What are the open bugs?"
    mock_chat.get_messages.return_value = [mock_message]

    # AI interprets as ticket request
    mock_ai.generate_response.return_value = "JIRA:SEARCH_TICKETS:status=open"

    # Jira returns tickets
    ticket = Mock()
    ticket.id = "BUG-100"
    ticket.title = "Critical bug"
    ticket.description = "Production issue"
    ticket.status = TicketStatus.OPEN
    mock_jira.search_tickets.return_value = [ticket]

    mock_chat.send_message.return_value = True

    # Create orchestrator
    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_jira,  # Use ticket_client for handle_message path
    )

    # Execute complete workflow
    result = orch.handle_message("channel_1", "msg_123")

    # Verify complete flow
    assert result is True

    # 1. Chat client retrieved message
    mock_chat.get_messages.assert_called_once_with("channel_1", limit=100)

    # 2. AI processed the message
    mock_ai.generate_response.assert_called_once()

    # 3. Ticket system was queried
    mock_jira.search_tickets.assert_called_once()

    # 4. Response was sent back to chat
    mock_chat.send_message.assert_called_once()
    sent_message = mock_chat.send_message.call_args[0][1]
    assert "BUG-100" in sent_message
    assert "Critical bug" in sent_message


@pytest.mark.integration
def test_orchestrator_metrics_tracking_across_workflow() -> None:
    """Test orchestrator tracks metrics through complete workflow."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    mock_message = Mock()
    mock_message.id = "msg_1"
    mock_message.content = "Show tickets"
    mock_chat.get_messages.return_value = [mock_message]

    mock_ai.generate_response.return_value = "JIRA:GET_TICKETS:limit=1"

    ticket = Mock()
    ticket.id = "T-1"
    ticket.title = "Test"
    ticket.description = "Test"
    ticket.status = TicketStatus.OPEN
    mock_jira.search_tickets.return_value = [ticket]

    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
    )

    # Initial metrics should be zero
    initial_metrics = orch.get_metrics()
    assert initial_metrics["total_requests"] == 0
    assert initial_metrics["successful_requests"] == 0

    # Execute workflow
    result = orch.handle_message("channel_1", "msg_1")
    assert result is True

    # Verify metrics were updated
    final_metrics = orch.get_metrics()
    assert final_metrics["total_requests"] == 1
    assert final_metrics["successful_requests"] == 1
    assert final_metrics["success_rate"] == 1.0
    assert final_metrics["average_latency_seconds"] > 0


@pytest.mark.integration
def test_orchestrator_handles_ai_failure_in_workflow() -> None:
    """Test orchestrator handles AI failure gracefully in full workflow."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()

    mock_message = Mock()
    mock_message.id = "msg_1"
    mock_message.content = "Test"
    mock_chat.get_messages.return_value = [mock_message]

    # AI fails
    mock_ai.generate_response.side_effect = RuntimeError("AI service down")

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
    )

    # Workflow should fail gracefully
    result = orch.handle_message("channel_1", "msg_1")

    assert result is False

    # Chat send should not have been called
    mock_chat.send_message.assert_not_called()

    # Metrics should track failure
    metrics = orch.get_metrics()
    assert metrics["failed_requests"] == 1
    assert metrics["failure_rate"] == 1.0


@pytest.mark.integration
def test_orchestrator_handles_chat_send_failure() -> None:
    """Test orchestrator handles chat send failure in workflow."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()

    mock_message = Mock()
    mock_message.id = "msg_1"
    mock_message.content = "Test"
    mock_chat.get_messages.return_value = [mock_message]

    mock_ai.generate_response.return_value = "AI response"

    # Chat send fails
    mock_chat.send_message.return_value = False

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
    )

    result = orch.handle_message("channel_1", "msg_1")

    # Workflow should report failure
    assert result is False

    # But AI should have been called
    mock_ai.generate_response.assert_called_once()

    # Metrics should track failure
    metrics = orch.get_metrics()
    assert metrics["failed_requests"] == 1


@pytest.mark.integration
def test_orchestrator_with_discord_and_jira() -> None:
    """Test orchestrator integrating Discord chat with Jira tickets."""
    from ai_chat_orchestrator.factory import create_gemini_discord_orchestrator

    # Create orchestrator with real factory
    orch = create_gemini_discord_orchestrator(gemini_api_key="test_key")

    # Verify components are properly wired
    assert orch.ai_client is not None
    assert orch.chat_client is not None

    # Add Jira client - need both ticket_client (for handle_message check) and jira_client (for JIRA: prefix handling)
    mock_jira = Mock()
    orch.ticket_client = mock_jira
    orch.jira_client = mock_jira

    # Setup mocks for workflow
    with patch.object(orch.chat_client, "get_messages") as mock_get:
        mock_message = Mock()
        mock_message.id = "discord_msg_1"
        mock_message.content = "Show Jira tickets"
        mock_get.return_value = [mock_message]

        with patch.object(orch.ai_client, "generate_response") as mock_ai:
            mock_ai.return_value = "JIRA:GET_TICKETS:limit=2"

            ticket = Mock()
            ticket.id = "DISC-1"
            ticket.title = "Discord integration"
            ticket.description = "Test"
            ticket.status = TicketStatus.OPEN
            mock_jira.search_tickets.return_value = [ticket]

            with patch.object(orch.chat_client, "send_message") as mock_send:
                mock_send.return_value = True

                result = orch.handle_message("discord_channel_1", "discord_msg_1")

                assert result is True
                # Verify Jira was called
                mock_jira.search_tickets.assert_called_once()


@pytest.mark.integration
def test_orchestrator_process_direct_full_workflow() -> None:
    """Test process_direct method with complete workflow including conversation history."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_gtasks = Mock()

    mock_ai.generate_response.return_value = "GTASKS:GET_TICKETS:limit=1"

    task = Mock()
    task.id = "task-x"
    task.title = "Test task"
    task.description = "Description"
    task.status = TicketStatus.OPEN
    mock_gtasks.search_tickets.return_value = [task]

    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        gtasks_client=mock_gtasks,
    )

    # First message
    result1 = orch.process_direct("channel_1", "Show me my tasks")
    assert result1 is not None
    assert "task-x" in result1

    # Conversation history should be saved
    assert "channel_1" in orch.conversation_history
    assert len(orch.conversation_history["channel_1"]) == 1

    # Second message - should include history
    mock_ai.generate_response.return_value = "The task task-x is important."
    orch.process_direct("channel_1", "What about the first one?")

    # History should be passed to AI
    call_args = mock_ai.generate_response.call_args_list[-1]
    assert "history" in call_args[1]["user_input"].lower() or "task-x" in call_args[1]["user_input"]

    # History should have 2 entries now
    assert len(orch.conversation_history["channel_1"]) == 2


@pytest.mark.integration
def test_orchestrator_handles_empty_ticket_response() -> None:
    """Test orchestrator handles empty ticket list gracefully."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    mock_ai.generate_response.return_value = "JIRA:GET_TICKETS:limit=5"

    # No tickets found
    mock_jira.search_tickets.return_value = []

    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
    )

    result = orch.process_direct("channel_1", "Show me tickets")

    assert result is not None
    assert "no tickets found" in result.lower()


@pytest.mark.integration
def test_orchestrator_multiple_sequential_requests() -> None:
    """Test orchestrator handles multiple sequential requests correctly."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
    )

    # Request 1: Get open tickets
    mock_ai.generate_response.return_value = "JIRA:SEARCH_TICKETS:status=open"

    ticket1 = Mock()
    ticket1.id = "T-1"
    ticket1.title = "Open"
    ticket1.description = "Test"
    ticket1.status = TicketStatus.OPEN
    mock_jira.search_tickets.return_value = [ticket1]

    result1 = orch.process_direct("channel_1", "Show open tickets")
    assert "T-1" in result1

    # Request 2: Get closed tickets
    mock_ai.generate_response.return_value = "JIRA:SEARCH_TICKETS:status=closed"

    ticket2 = Mock()
    ticket2.id = "T-2"
    ticket2.title = "Closed"
    ticket2.description = "Test"
    ticket2.status = TicketStatus.CLOSED
    mock_jira.search_tickets.return_value = [ticket2]

    result2 = orch.process_direct("channel_1", "Show closed tickets")
    assert "T-2" in result2

    # Verify metrics for both requests
    metrics = orch.get_metrics()
    assert metrics["total_requests"] == 2
    assert metrics["successful_requests"] == 2
