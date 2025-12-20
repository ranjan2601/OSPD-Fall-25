"""Integration tests for ticketing functionality in orchestrator service."""

import pytest
from unittest.mock import patch, MagicMock
import sys


@pytest.fixture(autouse=True)
def reset_orchestrator_state():
    """Reset orchestrator service state before each test."""
    # Remove orchestrator_service from cache if it exists
    if "orchestrator_service.api" in sys.modules:
        api_module = sys.modules["orchestrator_service.api"]
        api_module._jira_ticket_client = None
        api_module._gtasks_ticket_client = None
    yield
    # Clean up after test
    if "orchestrator_service.api" in sys.modules:
        api_module = sys.modules["orchestrator_service.api"]
        api_module._jira_ticket_client = None
        api_module._gtasks_ticket_client = None


@pytest.mark.integration
def test_jira_ticket_client_creation() -> None:
    """Test creating Jira ticket client."""
    mock_adapter = MagicMock()
    with patch("ticket_api.StandardizedTicketAdapter", return_value=mock_adapter):
        from orchestrator_service.api import get_jira_ticket_client

        client = get_jira_ticket_client()
        assert client is not None


@pytest.mark.integration
def test_gtasks_ticket_client_creation() -> None:
    """Test creating Google Tasks ticket client."""
    mock_client = MagicMock()
    # Patch at the location where it's imported/used
    with patch("orchestrator_service.api.TicketsClient", return_value=mock_client):
        from orchestrator_service.api import get_gtasks_ticket_client

        client = get_gtasks_ticket_client()
        assert client is not None
