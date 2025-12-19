"""Unit tests for orchestrator service API endpoints."""

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_orchestrator() -> Mock:
    """Create a mock orchestrator."""
    mock = Mock()
    mock.process_direct.return_value = "AI response"
    mock.chat_client = Mock()
    mock.get_metrics.return_value = {
        "total_requests": 10,
        "successful_requests": 8,
        "failed_requests": 2,
        "success_rate": 0.8,
        "failure_rate": 0.2,
        "average_latency_seconds": 1.5,
    }
    return mock


@pytest.fixture
def app_client() -> TestClient:
    """Create FastAPI test client."""
    from fastapi import FastAPI
    from orchestrator_service.api import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_healthy_status(self, app_client: Any) -> None:
        """Test health endpoint returns healthy status."""
        response = app_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data


class TestErrorHandling:
    """Test error handling in various endpoints."""

    def test_discord_process_exception_handling(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test Discord process endpoint handles exceptions properly."""
        mock_orchestrator.process_direct.side_effect = Exception("Test error")

        with patch("orchestrator_service.api.get_discord_orchestrator", return_value=mock_orchestrator):
            response = app_client.post(
                "/discord/process",
                json={"channel_id": "channel123", "user_input": "Hello"},
            )

            assert response.status_code == 500

    def test_slack_process_exception_handling(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test Slack process endpoint handles exceptions properly."""
        mock_orchestrator.process_direct.side_effect = Exception("Test error")

        with patch("orchestrator_service.api.get_slack_orchestrator", return_value=mock_orchestrator):
            response = app_client.post(
                "/slack/process",
                json={"channel_id": "C123", "user_input": "Hello"},
            )

            assert response.status_code == 500

    def test_jira_create_ticket_exception_handling(self, app_client: Any) -> None:
        """Test Jira create ticket handles exceptions."""
        mock_async_client = Mock()
        mock_async_client.create_ticket = AsyncMock(side_effect=Exception("Jira error"))

        with patch("orchestrator_service.api.get_jira_async_ticket_client", return_value=mock_async_client):
            response = app_client.post(
                "/jira/tickets",
                json={"title": "Test", "description": "Test"},
            )

            assert response.status_code == 500

    def test_gtasks_create_ticket_exception_handling(self, app_client: Any) -> None:
        """Test GTasks create ticket handles exceptions."""
        mock_client = Mock()
        mock_client.create_ticket.side_effect = Exception("GTasks error")

        with patch("orchestrator_service.api.get_gtasks_ticket_client", return_value=mock_client):
            response = app_client.post(
                "/gtasks/tickets",
                json={"title": "Test", "description": "Test"},
            )

            assert response.status_code == 500

    def test_discord_channels_exception_handling(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test Discord channels endpoint handles exceptions."""
        mock_orchestrator.chat_client.get_channels.side_effect = Exception("Channel error")

        with patch("orchestrator_service.api.get_discord_orchestrator", return_value=mock_orchestrator):
            response = app_client.get("/discord/channels")

            assert response.status_code == 500

    def test_slack_channels_exception_handling(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test Slack channels endpoint handles exceptions."""
        mock_orchestrator.chat_client.get_channels.side_effect = Exception("Channel error")

        with patch("orchestrator_service.api.get_slack_orchestrator", return_value=mock_orchestrator):
            response = app_client.get("/slack/channels")

            assert response.status_code == 500

    def test_jira_get_ticket_exception_handling(self, app_client: Any) -> None:
        """Test Jira get ticket handles exceptions (non-404)."""
        valid_uuid = "12345678-1234-5678-1234-567812345678"
        mock_async_client = Mock()
        mock_async_client.get_ticket = AsyncMock(side_effect=Exception("Database error"))

        with patch("orchestrator_service.api.get_jira_async_ticket_client", return_value=mock_async_client):
            response = app_client.get(f"/jira/tickets/{valid_uuid}")

            assert response.status_code == 500

    def test_gtasks_get_ticket_exception_handling(self, app_client: Any) -> None:
        """Test GTasks get ticket handles exceptions (non-404)."""
        mock_client = Mock()
        mock_client.get_ticket.side_effect = Exception("API error")

        with patch("orchestrator_service.api.get_gtasks_ticket_client", return_value=mock_client):
            response = app_client.get("/gtasks/tickets/task-123")

            assert response.status_code == 500

    def test_jira_search_tickets_exception_handling(self, app_client: Any) -> None:
        """Test Jira search tickets handles exceptions."""
        mock_async_client = Mock()
        mock_async_client.search_tickets = AsyncMock(side_effect=Exception("Search error"))

        with patch("orchestrator_service.api.get_jira_async_ticket_client", return_value=mock_async_client):
            response = app_client.get("/jira/tickets")

            assert response.status_code == 500

    def test_gtasks_search_tickets_exception_handling(self, app_client: Any) -> None:
        """Test GTasks search tickets handles exceptions."""
        mock_client = Mock()
        mock_client.search_tickets.side_effect = Exception("Search error")

        with patch("orchestrator_service.api.get_gtasks_ticket_client", return_value=mock_client):
            response = app_client.get("/gtasks/tickets")

            assert response.status_code == 500

    def test_discord_metrics_exception_handling(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test Discord metrics endpoint handles exceptions."""
        mock_orchestrator.get_metrics.side_effect = Exception("Metrics error")

        with patch("orchestrator_service.api.get_discord_orchestrator", return_value=mock_orchestrator):
            response = app_client.get("/discord/metrics")

            assert response.status_code == 500

    def test_slack_metrics_exception_handling(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test Slack metrics endpoint handles exceptions."""
        mock_orchestrator.get_metrics.side_effect = Exception("Metrics error")

        with patch("orchestrator_service.api.get_slack_orchestrator", return_value=mock_orchestrator):
            response = app_client.get("/slack/metrics")

            assert response.status_code == 500


class TestDiscordEndpoints:
    """Test Discord-related endpoints."""

    def test_process_discord_message_success(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test processing Discord message successfully."""
        with patch("orchestrator_service.api.get_discord_orchestrator", return_value=mock_orchestrator):
            response = app_client.post(
                "/discord/process",
                json={"channel_id": "channel123", "user_input": "Hello AI"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "AI response"
            assert data["success"] is True

    def test_process_discord_message_returns_none(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test processing Discord message when orchestrator returns None."""
        mock_orchestrator.process_direct.return_value = None

        with patch("orchestrator_service.api.get_discord_orchestrator", return_value=mock_orchestrator):
            response = app_client.post(
                "/discord/process",
                json={"channel_id": "channel123", "user_input": "Hello"},
            )

            assert response.status_code == 500

    def test_get_discord_channels_success(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test getting Discord channels."""
        mock_channel = Mock()
        mock_channel.id = "channel123"
        mock_channel.name = "general"
        mock_orchestrator.chat_client.get_channels.return_value = [mock_channel]

        with patch("orchestrator_service.api.get_discord_orchestrator", return_value=mock_orchestrator):
            response = app_client.get("/discord/channels")

            assert response.status_code == 200
            data = response.json()
            assert "channels" in data
            assert len(data["channels"]) == 1

    def test_send_discord_message_success(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test sending message to Discord channel."""
        mock_orchestrator.chat_client.send_message.return_value = True

        with patch("orchestrator_service.api.get_discord_orchestrator", return_value=mock_orchestrator):
            response = app_client.post(
                "/discord/channels/channel123/messages",
                json={"content": "Hello Discord!"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_get_discord_metrics_success(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test getting Discord orchestrator metrics."""
        with patch("orchestrator_service.api.get_discord_orchestrator", return_value=mock_orchestrator):
            response = app_client.get("/discord/metrics")

            assert response.status_code == 200
            data = response.json()
            # Metrics are wrapped in a metrics key
            assert "metrics" in data
            metrics = data["metrics"]
            assert metrics["total_requests"] == 10


class TestSlackEndpoints:
    """Test Slack-related endpoints."""

    def test_process_slack_message_success(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test processing Slack message successfully."""
        with patch("orchestrator_service.api.get_slack_orchestrator", return_value=mock_orchestrator):
            response = app_client.post(
                "/slack/process",
                json={"channel_id": "C123456", "user_input": "Hello Slack"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "AI response"

    def test_get_slack_metrics_success(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test getting Slack orchestrator metrics."""
        with patch("orchestrator_service.api.get_slack_orchestrator", return_value=mock_orchestrator):
            response = app_client.get("/slack/metrics")

            assert response.status_code == 200
            data = response.json()
            assert "metrics" in data

    def test_get_slack_channels_success(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test getting Slack channels."""
        mock_channel = Mock()
        mock_channel.id = "C123456"  # Changed from channel_id to id
        mock_channel.name = "general"
        mock_orchestrator.chat_client.get_channels.return_value = [mock_channel]

        with patch("orchestrator_service.api.get_slack_orchestrator", return_value=mock_orchestrator):
            response = app_client.get("/slack/channels")

            assert response.status_code == 200
            data = response.json()
            assert "channels" in data
            assert len(data["channels"]) == 1

    def test_send_slack_message_success(self, app_client: Any, mock_orchestrator: Any) -> None:
        """Test sending message to Slack channel."""
        mock_orchestrator.chat_client.send_message.return_value = True

        with patch("orchestrator_service.api.get_slack_orchestrator", return_value=mock_orchestrator):
            response = app_client.post(
                "/slack/channels/C123456/messages",
                json={"content": "Hello Slack!"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True


class TestJiraEndpoints:
    """Test Jira ticket-related endpoints."""

    def test_create_jira_ticket_success(self, app_client: Any) -> None:
        """Test creating a Jira ticket."""
        from tickets_api import Ticket, TicketStatus

        mock_ticket = Mock(spec=Ticket)
        mock_ticket.id = "12345678-1234-5678-1234-567812345678"  # Valid UUID
        mock_ticket.title = "Test ticket"
        mock_ticket.description = "Test description"
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket.assignee = "user@example.com"

        mock_async_client = Mock()
        mock_async_client.create_ticket = AsyncMock(return_value=mock_ticket)

        with patch("orchestrator_service.api.get_jira_async_ticket_client", return_value=mock_async_client):
            response = app_client.post(
                "/jira/tickets",
                json={
                    "title": "Test ticket",
                    "description": "Test description",
                    "assignee": "user@example.com",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "Test ticket"

    def test_get_jira_ticket_success(self, app_client: Any) -> None:
        """Test getting a Jira ticket by ID."""
        from tickets_api import Ticket, TicketStatus

        valid_uuid = "12345678-1234-5678-1234-567812345678"
        mock_ticket = Mock(spec=Ticket)
        mock_ticket.id = valid_uuid
        mock_ticket.title = "Test ticket"
        mock_ticket.description = "Test description"
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket.assignee = "user@example.com"

        mock_async_client = Mock()
        mock_async_client.get_ticket = AsyncMock(return_value=mock_ticket)

        with patch("orchestrator_service.api.get_jira_async_ticket_client", return_value=mock_async_client):
            response = app_client.get(f"/jira/tickets/{valid_uuid}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == valid_uuid

    def test_get_jira_ticket_not_found(self, app_client: Any) -> None:
        """Test getting non-existent Jira ticket."""
        valid_uuid = "12345678-1234-5678-1234-567812345678"
        mock_async_client = Mock()
        mock_async_client.get_ticket = AsyncMock(return_value=None)

        with patch("orchestrator_service.api.get_jira_async_ticket_client", return_value=mock_async_client):
            response = app_client.get(f"/jira/tickets/{valid_uuid}")

            assert response.status_code == 404

    def test_list_jira_tickets_success(self, app_client: Any) -> None:
        """Test listing Jira tickets."""
        from tickets_api import Ticket, TicketStatus

        mock_ticket = Mock(spec=Ticket)
        mock_ticket.id = "12345678-1234-5678-1234-567812345678"
        mock_ticket.title = "Test ticket"
        mock_ticket.description = "Test description"
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket.assignee = "user@example.com"

        mock_async_client = Mock()
        mock_async_client.search_tickets = AsyncMock(return_value=[mock_ticket])

        with patch("orchestrator_service.api.get_jira_async_ticket_client", return_value=mock_async_client):
            response = app_client.get("/jira/tickets")

            assert response.status_code == 200
            data = response.json()
            assert "tickets" in data
            assert len(data["tickets"]) == 1


class TestGTasksEndpoints:
    """Test Google Tasks ticket-related endpoints."""

    def test_create_gtasks_ticket_success(self, app_client: Any) -> None:
        """Test creating a Google Tasks ticket."""
        from tickets_api import Ticket as GTTicket
        from tickets_api import TicketStatus as GTTicketStatus

        mock_ticket = Mock(spec=GTTicket)
        mock_ticket.id = "task-123"
        mock_ticket.title = "Test task"
        mock_ticket.description = "Test description"
        mock_ticket.status = GTTicketStatus.OPEN
        mock_ticket.assignee = None

        mock_client = Mock()
        mock_client.create_ticket.return_value = mock_ticket

        with patch("orchestrator_service.api.get_gtasks_ticket_client", return_value=mock_client):
            response = app_client.post(
                "/gtasks/tickets",
                json={
                    "title": "Test task",
                    "description": "Test description",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "task-123"
            assert data["title"] == "Test task"

    def test_get_gtasks_ticket_success(self, app_client: Any) -> None:
        """Test getting a Google Tasks ticket by ID."""
        from tickets_api import Ticket as GTTicket
        from tickets_api import TicketStatus as GTTicketStatus

        mock_ticket = Mock(spec=GTTicket)
        mock_ticket.id = "task-123"
        mock_ticket.title = "Test task"
        mock_ticket.description = "Test description"
        mock_ticket.status = GTTicketStatus.OPEN
        mock_ticket.assignee = None

        mock_client = Mock()
        mock_client.get_ticket.return_value = mock_ticket

        with patch("orchestrator_service.api.get_gtasks_ticket_client", return_value=mock_client):
            response = app_client.get("/gtasks/tickets/task-123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "task-123"

    def test_get_gtasks_ticket_not_found(self, app_client: Any) -> None:
        """Test getting non-existent Google Tasks ticket."""
        mock_client = Mock()
        mock_client.get_ticket.return_value = None

        with patch("orchestrator_service.api.get_gtasks_ticket_client", return_value=mock_client):
            response = app_client.get("/gtasks/tickets/task-999")

            assert response.status_code == 404

    def test_list_gtasks_tickets_success(self, app_client: Any) -> None:
        """Test listing Google Tasks tickets."""
        from tickets_api import Ticket as GTTicket
        from tickets_api import TicketStatus as GTTicketStatus

        mock_ticket = Mock(spec=GTTicket)
        mock_ticket.id = "task-123"
        mock_ticket.title = "Test task"
        mock_ticket.description = "Test description"
        mock_ticket.status = GTTicketStatus.OPEN
        mock_ticket.assignee = None

        mock_client = Mock()
        mock_client.search_tickets.return_value = [mock_ticket]

        with patch("orchestrator_service.api.get_gtasks_ticket_client", return_value=mock_client):
            response = app_client.get("/gtasks/tickets")

            assert response.status_code == 200
            data = response.json()
            assert "tickets" in data
            assert len(data["tickets"]) == 1


class TestTicketSearchEndpoints:
    """Test ticket search functionality with filters."""

    def test_search_jira_tickets_with_query(self, app_client: Any) -> None:
        """Test searching Jira tickets with query parameter."""
        from tickets_api import Ticket, TicketStatus

        mock_ticket = Mock(spec=Ticket)
        mock_ticket.id = "12345678-1234-5678-1234-567812345678"
        mock_ticket.title = "Bug fix"
        mock_ticket.description = "Fix the bug"
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket.assignee = "dev@example.com"

        mock_async_client = Mock()
        mock_async_client.search_tickets = AsyncMock(return_value=[mock_ticket])

        with patch("orchestrator_service.api.get_jira_async_ticket_client", return_value=mock_async_client):
            response = app_client.get("/jira/tickets?query=bug")

            assert response.status_code == 200
            data = response.json()
            assert len(data["tickets"]) == 1
            assert data["tickets"][0]["title"] == "Bug fix"

    def test_search_jira_tickets_with_status(self, app_client: Any) -> None:
        """Test searching Jira tickets with status filter."""
        from tickets_api import Ticket, TicketStatus

        mock_ticket = Mock(spec=Ticket)
        mock_ticket.id = "12345678-1234-5678-1234-567812345678"
        mock_ticket.title = "Active task"
        mock_ticket.description = "Task description"
        mock_ticket.status = TicketStatus.IN_PROGRESS
        mock_ticket.assignee = "dev@example.com"

        mock_async_client = Mock()
        mock_async_client.search_tickets = AsyncMock(return_value=[mock_ticket])

        with patch("orchestrator_service.api.get_jira_async_ticket_client", return_value=mock_async_client):
            # Use the correct enum value "in_progress" not "IN_PROGRESS"
            response = app_client.get("/jira/tickets?status=in_progress")

            assert response.status_code == 200
            data = response.json()
            assert len(data["tickets"]) == 1

    def test_search_gtasks_tickets_with_query(self, app_client: Any) -> None:
        """Test searching Google Tasks tickets with query parameter."""
        from tickets_api import Ticket as GTTicket
        from tickets_api import TicketStatus as GTTicketStatus

        mock_ticket = Mock(spec=GTTicket)
        mock_ticket.id = "task-456"
        mock_ticket.title = "Important task"
        mock_ticket.description = "Do this task"
        mock_ticket.status = GTTicketStatus.OPEN
        mock_ticket.assignee = None

        mock_client = Mock()
        mock_client.search_tickets.return_value = [mock_ticket]

        with patch("orchestrator_service.api.get_gtasks_ticket_client", return_value=mock_client):
            response = app_client.get("/gtasks/tickets?query=important")

            assert response.status_code == 200
            data = response.json()
            assert len(data["tickets"]) == 1
            assert data["tickets"][0]["title"] == "Important task"
