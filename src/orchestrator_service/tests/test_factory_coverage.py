"""Tests for orchestrator service factory functions."""

import os
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test-key",
            "DISCORD_USER_ID": "user123",
            "SLACK_BOT_TOKEN": "xoxb-test",
            "JIRA_USER_ID": "jira-user",
            "JIRA_PROJECT_KEY": "TEST",
        },
    ):
        yield


@patch("orchestrator_service.api.get_jira_ticket_client")
@patch("orchestrator_service.api.GeminiClient")
@patch("orchestrator_service.api.chat_client_api.get_client")
@patch("orchestrator_service.api.AIChatOrchestrator")
def test_get_discord_orchestrator_creates_instance(
    mock_orch, mock_get_client, mock_gemini, mock_jira, mock_env
):
    """Test Discord orchestrator creation."""
    from orchestrator_service import api
    
    # Reset global state
    api._discord_orchestrator = None
    
    mock_chat = MagicMock()
    mock_get_client.return_value = mock_chat
    mock_ai = MagicMock()
    mock_gemini.return_value = mock_ai
    mock_jira.side_effect = Exception("Jira not configured")
    mock_orch_instance = MagicMock()
    mock_orch.return_value = mock_orch_instance
    
    result = api.get_discord_orchestrator()
    
    assert result == mock_orch_instance
    mock_gemini.assert_called_once()


@patch("orchestrator_service.api.GeminiClient")
@patch("orchestrator_service.api.chat_client_api.get_client")
def test_get_discord_orchestrator_caches_instance(mock_get_client, mock_gemini, mock_env):
    """Test Discord orchestrator is cached."""
    from orchestrator_service import api
    
    # Set cached instance
    cached = MagicMock()
    api._discord_orchestrator = cached
    
    result = api.get_discord_orchestrator()
    
    assert result == cached
    mock_gemini.assert_not_called()
    mock_get_client.assert_not_called()


@patch("orchestrator_service.api.resolve_api_key")
def test_get_discord_orchestrator_missing_api_key(mock_resolve, mock_env):
    """Test Discord orchestrator with missing API key."""
    from fastapi import HTTPException

    from orchestrator_service import api
    
    api._discord_orchestrator = None
    mock_resolve.side_effect = ValueError("No API key")
    
    with pytest.raises(HTTPException) as exc_info:
        api.get_discord_orchestrator()
    
    assert exc_info.value.status_code == 500


@patch("orchestrator_service.api.GeminiClient")
@patch("orchestrator_service.api.SlackChatClient")
@patch("orchestrator_service.api.AIChatOrchestrator")
def test_get_slack_orchestrator_creates_instance(
    mock_orch, mock_slack, mock_gemini, mock_env
):
    """Test Slack orchestrator creation."""
    from orchestrator_service import api
    
    api._slack_orchestrator = None
    
    mock_chat = MagicMock()
    mock_slack.return_value = mock_chat
    mock_ai = MagicMock()
    mock_gemini.return_value = mock_ai
    mock_orch_instance = MagicMock()
    mock_orch.return_value = mock_orch_instance
    
    result = api.get_slack_orchestrator()
    
    assert result == mock_orch_instance
    mock_gemini.assert_called_once()
    mock_slack.assert_called_once()


@patch("orchestrator_service.api.GeminiClient")
@patch("orchestrator_service.api.SlackChatClient")
def test_get_slack_orchestrator_caches_instance(mock_slack, mock_gemini, mock_env):
    """Test Slack orchestrator is cached."""
    from orchestrator_service import api
    
    cached = MagicMock()
    api._slack_orchestrator = cached
    
    result = api.get_slack_orchestrator()
    
    assert result == cached
    mock_gemini.assert_not_called()
    mock_slack.assert_not_called()


@patch("orchestrator_service.api.resolve_api_key")
def test_get_slack_orchestrator_missing_api_key(mock_resolve, mock_env):
    """Test Slack orchestrator with missing API key."""
    from fastapi import HTTPException

    from orchestrator_service import api
    
    api._slack_orchestrator = None
    mock_resolve.side_effect = ValueError("No API key")
    
    with pytest.raises(HTTPException) as exc_info:
        api.get_slack_orchestrator()
    
    assert exc_info.value.status_code == 500


@patch("orchestrator_service.api.TicketImpl")
@patch("orchestrator_service.api.StandardizedTicketAdapter")
def test_get_jira_ticket_client_creates_instance(mock_adapter, mock_impl, mock_env):
    """Test Jira ticket client creation."""
    from orchestrator_service import api
    
    api._jira_ticket_client = None
    
    mock_jira = MagicMock()
    mock_impl.return_value = mock_jira
    mock_adapted = MagicMock()
    mock_adapter.return_value = mock_adapted
    
    result = api.get_jira_ticket_client()
    
    assert result == mock_adapted
    mock_impl.assert_called_once()
    mock_adapter.assert_called_once_with(mock_jira)


@patch("orchestrator_service.api.TicketImpl")
@patch("orchestrator_service.api.StandardizedTicketAdapter")
def test_get_jira_ticket_client_caches_instance(mock_adapter, mock_impl, mock_env):
    """Test Jira ticket client is cached."""
    from orchestrator_service import api
    
    cached = MagicMock()
    api._jira_ticket_client = cached
    
    result = api.get_jira_ticket_client()
    
    assert result == cached
    mock_impl.assert_not_called()
    mock_adapter.assert_not_called()


@patch("orchestrator_service.api.TicketImpl")
def test_get_jira_ticket_client_init_error(mock_impl, mock_env):
    """Test Jira ticket client with initialization error."""
    from fastapi import HTTPException

    from orchestrator_service import api
    
    api._jira_ticket_client = None
    mock_impl.side_effect = ValueError("Init failed")
    
    with pytest.raises(HTTPException) as exc_info:
        api.get_jira_ticket_client()
    
    assert exc_info.value.status_code == 500


@patch("orchestrator_service.api.TicketsClient")
def test_get_gtasks_ticket_client_creates_instance(mock_impl, mock_env):
    """Test Google Tasks ticket client creation."""
    from orchestrator_service import api
    
    api._gtasks_ticket_client = None
    
    mock_gtasks = MagicMock()
    mock_impl.return_value = mock_gtasks
    
    result = api.get_gtasks_ticket_client()
    
    assert result == mock_gtasks
    mock_impl.assert_called_once()


@patch("orchestrator_service.api.TicketsClient")
def test_get_gtasks_ticket_client_caches_instance(mock_impl, mock_env):
    """Test Google Tasks ticket client is cached."""
    from orchestrator_service import api
    
    cached = MagicMock()
    api._gtasks_ticket_client = cached
    
    result = api.get_gtasks_ticket_client()
    
    assert result == cached
    mock_impl.assert_not_called()


@patch("orchestrator_service.api.TicketsClient")
def test_get_gtasks_ticket_client_init_error(mock_impl, mock_env):
    """Test Google Tasks ticket client with initialization error."""
    from fastapi import HTTPException

    from orchestrator_service import api
    
    api._gtasks_ticket_client = None
    mock_impl.side_effect = ValueError("Init failed")
    
    with pytest.raises(HTTPException) as exc_info:
        api.get_gtasks_ticket_client()
    
    assert exc_info.value.status_code == 500

