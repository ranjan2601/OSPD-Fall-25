"""Unit tests for orchestrator ticket handling functionality."""

from unittest.mock import Mock

from ai_chat_orchestrator import AIChatOrchestrator


def test_orchestrator_with_ticket_client() -> None:
    """Test orchestrator initialization with ticket client."""
    mock_ai = Mock()
    mock_chat = Mock()
    mock_ticket = Mock()

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    assert orchestrator.ticket_client == mock_ticket
    assert "ticketing/task management system" in orchestrator.system_prompt


def test_orchestrator_without_ticket_client() -> None:
    """Test orchestrator initialization without ticket client."""
    mock_ai = Mock()
    mock_chat = Mock()

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=None,
    )

    assert orchestrator.ticket_client is None
    assert "ticketing/task management system" not in orchestrator.system_prompt


def test_ticket_request_detection() -> None:
    """Test detection of ticket-related requests."""
    mock_ai = Mock()
    mock_chat = Mock()
    mock_ticket = Mock()

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    # Test GET_TICKETS detection
    assert orchestrator._is_ticket_request("GET_TICKETS:limit=5")
    assert orchestrator._is_ticket_request("SEARCH_TICKETS:status=open")
    assert orchestrator._is_ticket_request("GET_TICKET:id=123")

    # Test non-ticket requests
    assert not orchestrator._is_ticket_request("Hello world")
    assert not orchestrator._is_ticket_request("What's the weather?")


def test_handle_get_tickets_request() -> None:
    """Test handling GET_TICKETS command."""
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = [
        "GET_TICKETS:limit=3",  # AI returns ticket command
        "Here are your tickets: ticket1, ticket2",  # AI summary
    ]

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Show me my tickets"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_ticket = Mock()
    mock_ticket1 = Mock()
    mock_ticket1.id = "t1"
    mock_ticket1.title = "Bug"
    mock_ticket1.status = "open"
    mock_ticket1.description = "Fix the bug"

    mock_ticket2 = Mock()
    mock_ticket2.id = "t2"
    mock_ticket2.title = "Feature"
    mock_ticket2.status = "in_progress"
    mock_ticket2.description = "Add feature"

    mock_ticket.search_tickets.return_value = [mock_ticket1, mock_ticket2]

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    result = orchestrator.handle_message("channel1", "msg1")

    assert result is True
    assert mock_ticket.search_tickets.called
    assert mock_ai.generate_response.call_count == 2  # Initial + summary


def test_handle_search_tickets_request() -> None:
    """Test handling SEARCH_TICKETS command."""
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = [
        "SEARCH_TICKETS:status=open",
        "Found 2 open tickets",
    ]

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Show me open tickets"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_ticket = Mock()
    mock_ticket1 = Mock()
    mock_ticket1.id = "t1"
    mock_ticket1.title = "Bug"
    mock_ticket1.status = "open"
    mock_ticket1.description = "Open bug"

    mock_ticket.search_tickets.return_value = [mock_ticket1]

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    result = orchestrator.handle_message("channel1", "msg1")

    assert result is True
    mock_ticket.search_tickets.assert_called_once()


def test_handle_get_ticket_request() -> None:
    """Test handling GET_TICKET command for specific ticket."""
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = [
        "GET_TICKET:id=PROJ-123",
        "Here's ticket PROJ-123 details",
    ]

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Show me ticket PROJ-123"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_ticket_obj = Mock()
    mock_ticket_obj.id = "PROJ-123"
    mock_ticket_obj.title = "Fix bug"
    mock_ticket_obj.status = "open"
    mock_ticket_obj.description = "Critical bug fix"

    mock_ticket = Mock()
    mock_ticket.get_ticket.return_value = mock_ticket_obj

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    result = orchestrator.handle_message("channel1", "msg1")

    assert result is True
    mock_ticket.get_ticket.assert_called_once_with("PROJ-123")


def test_ticket_request_with_no_results() -> None:
    """Test ticket request that returns no results."""
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = [
        "GET_TICKETS:limit=5",
        "No tickets found",
    ]

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Show me tickets"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_ticket = Mock()
    mock_ticket.search_tickets.return_value = []  # No tickets

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    result = orchestrator.handle_message("channel1", "msg1")

    assert result is True


def test_ticket_request_error_handling() -> None:
    """Test error handling when ticket service fails."""
    mock_ai = Mock()
    mock_ai.generate_response.return_value = "GET_TICKETS:limit=5"

    mock_chat = Mock()
    mock_message = Mock()
    mock_message.id = "msg1"
    mock_message.content = "Show me tickets"
    mock_chat.get_messages.return_value = [mock_message]
    mock_chat.send_message.return_value = True

    mock_ticket = Mock()
    mock_ticket.search_tickets.side_effect = RuntimeError("Ticket service down")

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    # Should not crash, should handle gracefully
    result = orchestrator.handle_message("channel1", "msg1")

    # Should return True because the response was sent (even if ticket fetch failed)
    assert result is True


def test_process_direct_with_tickets() -> None:
    """Test process_direct method with ticket integration."""
    mock_ai = Mock()
    mock_ai.generate_response.side_effect = [
        "GET_TICKETS:limit=2",
        "Here are your 2 tickets",
    ]

    mock_chat = Mock()
    mock_chat.send_message.return_value = True

    mock_ticket1 = Mock()
    mock_ticket1.id = "t1"
    mock_ticket1.title = "Task 1"
    mock_ticket1.status = "open"
    mock_ticket1.description = "First task"

    mock_ticket2 = Mock()
    mock_ticket2.id = "t2"
    mock_ticket2.title = "Task 2"
    mock_ticket2.status = "open"
    mock_ticket2.description = "Second task"

    mock_ticket = Mock()
    mock_ticket.search_tickets.return_value = [mock_ticket1, mock_ticket2]

    orchestrator = AIChatOrchestrator(
        ai_client=mock_ai,
        chat_client=mock_chat,
        ticket_client=mock_ticket,
    )

    result = orchestrator.process_direct("channel1", "Show my tickets")

    assert result == "Here are your 2 tickets"
    assert mock_ticket.search_tickets.called

