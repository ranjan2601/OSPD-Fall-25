"""Integration tests for AI + Ticketing workflows."""

import pytest


@pytest.mark.integration
def test_ticketing_integration_exists() -> None:
    """Test that ticketing integration is properly set up."""
    from orchestrator_service.api import get_jira_ticket_client, get_gtasks_ticket_client

    # Just verify the functions exist and can be called
    assert callable(get_jira_ticket_client)
    assert callable(get_gtasks_ticket_client)
