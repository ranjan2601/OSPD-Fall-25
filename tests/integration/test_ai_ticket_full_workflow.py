"""Integration tests for AI + Ticketing System interaction.

Tests verify the complete workflow from AI interpretation to ticket operations,
demonstrating interaction between AI and Ticketing components.
"""

import pytest
from unittest.mock import Mock
from tickets_api import TicketStatus


@pytest.mark.integration
def test_ai_interprets_ticket_request_to_jira() -> None:
    """Test AI correctly interprets user request and fetches Jira tickets."""
    from ai_chat_orchestrator import AIChatOrchestrator

    # Setup mocks
    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    # Create mock ticket
    mock_ticket = Mock()
    mock_ticket.id = "PROJ-123"
    mock_ticket.title = "Bug in login"
    mock_ticket.description = "Users cannot log in"
    mock_ticket.status = TicketStatus.OPEN
    mock_ticket.assignee = "dev@example.com"

    # Setup AI to return a ticket command
    mock_ai.generate_response.return_value = "JIRA:GET_TICKETS:limit=5"

    # Setup Jira to return tickets
    mock_jira.search_tickets.return_value = [mock_ticket]

    # Setup chat to succeed
    mock_chat.send_message.return_value = True

    # Create orchestrator
    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
    )

    # Execute workflow
    result = orch.process_direct("channel_1", "Show me the latest tickets")

    # Verify AI was called
    assert mock_ai.generate_response.called
    assert "Show me the latest tickets" in str(mock_ai.generate_response.call_args)

    # Verify ticket system was queried
    mock_jira.search_tickets.assert_called_once_with(query=None, status=None)

    # Verify response contains ticket data
    assert result is not None
    assert "PROJ-123" in result
    assert "Bug in login" in result

    # Verify message was sent
    mock_chat.send_message.assert_called_once()
    sent_message = mock_chat.send_message.call_args[0][1]
    assert "PROJ-123" in sent_message


@pytest.mark.integration
def test_ai_filters_tickets_by_status() -> None:
    """Test AI interprets status filter and applies it to ticket search."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    # AI interprets "open tickets" as a status search
    mock_ai.generate_response.return_value = "JIRA:SEARCH_TICKETS:status=open"

    mock_ticket = Mock()
    mock_ticket.id = "PROJ-456"
    mock_ticket.title = "Open bug"
    mock_ticket.description = "This is open"
    mock_ticket.status = TicketStatus.OPEN

    mock_jira.search_tickets.return_value = [mock_ticket]
    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
    )

    result = orch.process_direct("channel_1", "Show me all open tickets")

    # Verify correct status filter was applied
    mock_jira.search_tickets.assert_called_once_with(query=None, status=TicketStatus.OPEN)

    # Verify ticket was returned
    assert "PROJ-456" in result
    assert "Open bug" in result


@pytest.mark.integration
def test_ai_retrieves_specific_ticket() -> None:
    """Test AI can retrieve a specific ticket by ID."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    # AI interprets ticket ID request - use valid UUID format
    valid_uuid = "12345678-1234-5678-1234-567812345678"
    mock_ai.generate_response.return_value = f"JIRA:GET_TICKET:id={valid_uuid}"

    mock_ticket = Mock()
    mock_ticket.id = valid_uuid
    mock_ticket.title = "Specific ticket"
    mock_ticket.description = "Details here"
    mock_ticket.status = TicketStatus.IN_PROGRESS

    mock_jira.get_ticket.return_value = mock_ticket
    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
    )

    result = orch.process_direct("channel_1", "Get ticket")

    # Verify get_ticket was called with correct ID (as string)
    mock_jira.get_ticket.assert_called_once_with(valid_uuid)

    assert valid_uuid in result
    assert "Specific ticket" in result


@pytest.mark.integration
def test_ai_switches_between_jira_and_gtasks() -> None:
    """Test AI can switch between Jira and Google Tasks based on user intent."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()
    mock_gtasks = Mock()

    # Setup mock tickets for both systems
    jira_ticket = Mock()
    jira_ticket.id = "PROJ-100"
    jira_ticket.title = "Jira task"
    jira_ticket.description = "Jira description"
    jira_ticket.status = TicketStatus.OPEN

    gtask_ticket = Mock()
    gtask_ticket.id = "task-200"
    gtask_ticket.title = "GTasks item"
    gtask_ticket.description = "GTasks description"
    gtask_ticket.status = TicketStatus.OPEN

    mock_jira.search_tickets.return_value = [jira_ticket]
    mock_gtasks.search_tickets.return_value = [gtask_ticket]
    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
        gtasks_client=mock_gtasks,
    )

    # Test 1: Request Jira tickets
    mock_ai.generate_response.return_value = "JIRA:GET_TICKETS:limit=5"
    result1 = orch.process_direct("channel_1", "Show me Jira tickets")

    assert mock_jira.search_tickets.called
    assert "PROJ-100" in result1
    assert "Jira task" in result1

    # Test 2: Request Google Tasks
    mock_ai.generate_response.return_value = "GTASKS:GET_TICKETS:limit=5"
    result2 = orch.process_direct("channel_1", "Show me my Google Tasks")

    assert mock_gtasks.search_tickets.called
    assert "task-200" in result2
    assert "GTasks item" in result2


@pytest.mark.integration
def test_ai_handles_ticket_system_error_gracefully() -> None:
    """Test AI handles ticket system errors and provides user-friendly message."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    # AI interprets request
    mock_ai.generate_response.return_value = "JIRA:GET_TICKETS:limit=5"

    # Jira throws an error
    mock_jira.search_tickets.side_effect = RuntimeError("Jira API down")

    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
    )

    result = orch.process_direct("channel_1", "Show me tickets")

    # Verify error message is user-friendly
    assert result is not None
    # The actual error message format is "Sorry, I couldn't complete the Jira operation right now. Error: ..."
    assert "couldn't complete" in result.lower() or "unavailable" in result.lower()
    assert "Jira" in result or "jira" in result.lower()

    # Verify message was still sent to user
    mock_chat.send_message.assert_called_once()


@pytest.mark.integration
def test_ai_and_tickets_with_conversation_context() -> None:
    """Test AI uses conversation history when handling ticket requests."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    mock_ticket = Mock()
    mock_ticket.id = "PROJ-999"
    mock_ticket.title = "Context-aware ticket"
    mock_ticket.description = "Test"
    mock_ticket.status = TicketStatus.OPEN

    mock_jira.search_tickets.return_value = [mock_ticket]
    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
    )

    # First interaction - get tickets
    mock_ai.generate_response.return_value = "JIRA:GET_TICKETS:limit=1"
    result1 = orch.process_direct("channel_1", "Show me a ticket")

    assert result1 is not None
    assert "PROJ-999" in result1

    # Second interaction - should have context from first
    mock_ai.generate_response.return_value = "The ticket PROJ-999 is open and needs attention."
    orch.process_direct("channel_1", "Tell me about it")

    # Verify AI received conversation history
    ai_call_args = mock_ai.generate_response.call_args_list[-1]
    user_input = ai_call_args[1]["user_input"]

    # Should contain history
    assert "Recent conversation history" in user_input or "PROJ-999" in user_input or "ticket" in user_input


@pytest.mark.integration
def test_ai_ticket_workflow_with_multiple_tickets() -> None:
    """Test AI handles multiple tickets and formats them correctly."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_chat = Mock()
    mock_jira = Mock()

    # Create multiple mock tickets
    tickets = []
    for i in range(3):
        ticket = Mock()
        ticket.id = f"PROJ-{i + 1}"
        ticket.title = f"Ticket {i + 1}"
        ticket.description = f"Description {i + 1}"
        ticket.status = TicketStatus.OPEN
        tickets.append(ticket)

    mock_ai.generate_response.return_value = "JIRA:GET_TICKETS:limit=3"
    mock_jira.search_tickets.return_value = tickets
    mock_chat.send_message.return_value = True

    orch = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        jira_client=mock_jira,
    )

    result = orch.process_direct("channel_1", "Show me 3 tickets")

    # Verify all tickets are in response
    assert "PROJ-1" in result
    assert "PROJ-2" in result
    assert "PROJ-3" in result

    # Verify numbering/formatting
    assert "1." in result or "1)" in result  # Should have numbered list

    # Verify count message
    assert "3" in result and "ticket" in result.lower()
