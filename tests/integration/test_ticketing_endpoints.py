"""Integration tests for ticketing functionality in orchestrator service."""

import pytest
from unittest.mock import patch


@pytest.mark.integration
def test_jira_ticket_client_creation() -> None:
    """Test creating Jira ticket client."""
    with patch("orchestrator_service.api.StandardizedTicketAdapter"):
        from orchestrator_service.api import get_jira_ticket_client
        import orchestrator_service.api as api_module

        api_module._jira_ticket_client = None
        client = get_jira_ticket_client()
        assert client is not None


@pytest.mark.integration
def test_gtasks_ticket_client_creation() -> None:
    """Test creating Google Tasks ticket client."""
    with patch("orchestrator_service.api.TicketsClient"):
        from orchestrator_service.api import get_gtasks_ticket_client
        import orchestrator_service.api as api_module

        api_module._gtasks_ticket_client = None
        client = get_gtasks_ticket_client()
        assert client is not None
