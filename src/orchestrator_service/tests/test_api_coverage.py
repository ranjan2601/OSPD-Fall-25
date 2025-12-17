"""Tests for orchestrator service API endpoints to increase coverage."""

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(
        os.environ,
        {
            "GEMINI_API_KEY": "test-key",
            "DISCORD_USER_ID": "test-user",
            "SLACK_BOT_TOKEN": "xoxb-test",
            "JIRA_USER_ID": "jira-user",
            "JIRA_PROJECT_KEY": "TEST",
        },
    ):
        yield


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator."""
    orchestrator = MagicMock()
    orchestrator.process_direct.return_value = "AI response"
    orchestrator.chat_client.get_channels.return_value = iter([])
    orchestrator.chat_client.send_message.return_value = True
    orchestrator.get_metrics.return_value = {"requests": 0}
    return orchestrator


@pytest.fixture
def client(mock_env_vars):
    """Create test client."""
    from orchestrator_service.api import router
    from fastapi import FastAPI
    
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "orchestrator" in data["service"].lower()


@patch("orchestrator_service.api.get_discord_orchestrator")
def test_process_discord_message_success(mock_get_orch, client, mock_orchestrator):
    """Test processing Discord message successfully."""
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.post(
        "/discord/process",
        json={"channel_id": "123", "user_input": "Hello"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["response"] == "AI response"


@patch("orchestrator_service.api.get_discord_orchestrator")
def test_process_discord_message_none_response(mock_get_orch, client, mock_orchestrator):
    """Test Discord message processing with None response."""
    mock_orchestrator.process_direct.return_value = None
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.post(
        "/discord/process",
        json={"channel_id": "123", "user_input": "Hello"},
    )
    
    assert response.status_code == 500


@patch("orchestrator_service.api.get_discord_orchestrator")
def test_process_discord_message_error(mock_get_orch, client):
    """Test Discord message processing with error."""
    mock_get_orch.side_effect = ValueError("Test error")
    
    response = client.post(
        "/discord/process",
        json={"channel_id": "123", "user_input": "Hello"},
    )
    
    assert response.status_code == 500


@patch("orchestrator_service.api.get_discord_orchestrator")
def test_get_discord_channels(mock_get_orch, client, mock_orchestrator):
    """Test getting Discord channels."""
    channel = MagicMock()
    channel.id = "123"
    channel.name = "general"
    mock_orchestrator.chat_client.get_channels.return_value = iter([channel])
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.get("/discord/channels")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["channels"]) == 1
    assert data["channels"][0]["id"] == "123"


@patch("orchestrator_service.api.get_discord_orchestrator")
def test_get_discord_channels_error(mock_get_orch, client, mock_orchestrator):
    """Test getting Discord channels with error."""
    mock_orchestrator.chat_client.get_channels.side_effect = ValueError("Test error")
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.get("/discord/channels")
    
    assert response.status_code == 500


@patch("orchestrator_service.api.get_discord_orchestrator")
def test_send_discord_message(mock_get_orch, client, mock_orchestrator):
    """Test sending Discord message."""
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.post(
        "/discord/channels/123/messages",
        json={"content": "Test message"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@patch("orchestrator_service.api.get_discord_orchestrator")
def test_send_discord_message_error(mock_get_orch, client, mock_orchestrator):
    """Test sending Discord message with error."""
    mock_orchestrator.chat_client.send_message.side_effect = ValueError("Test error")
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.post(
        "/discord/channels/123/messages",
        json={"content": "Test message"},
    )
    
    assert response.status_code == 500


@patch("orchestrator_service.api.get_discord_orchestrator")
def test_get_discord_metrics(mock_get_orch, client, mock_orchestrator):
    """Test getting Discord metrics."""
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.get("/discord/metrics")
    
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data


@patch("orchestrator_service.api.get_discord_orchestrator")
def test_get_discord_metrics_error(mock_get_orch, client):
    """Test getting Discord metrics with error."""
    mock_get_orch.side_effect = ValueError("Test error")
    
    response = client.get("/discord/metrics")
    
    assert response.status_code == 500


@patch("orchestrator_service.api.get_slack_orchestrator")
def test_process_slack_message_success(mock_get_orch, client, mock_orchestrator):
    """Test processing Slack message successfully."""
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.post(
        "/slack/process",
        json={"channel_id": "C123", "user_input": "Hello"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@patch("orchestrator_service.api.get_slack_orchestrator")
def test_process_slack_message_none_response(mock_get_orch, client, mock_orchestrator):
    """Test Slack message processing with None response."""
    mock_orchestrator.process_direct.return_value = None
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.post(
        "/slack/process",
        json={"channel_id": "C123", "user_input": "Hello"},
    )
    
    assert response.status_code == 500


@patch("orchestrator_service.api.get_slack_orchestrator")
def test_process_slack_message_error(mock_get_orch, client):
    """Test Slack message processing with error."""
    mock_get_orch.side_effect = ValueError("Test error")
    
    response = client.post(
        "/slack/process",
        json={"channel_id": "C123", "user_input": "Hello"},
    )
    
    assert response.status_code == 500


@patch("orchestrator_service.api.get_slack_orchestrator")
def test_get_slack_channels(mock_get_orch, client, mock_orchestrator):
    """Test getting Slack channels."""
    channel = MagicMock()
    channel.id = "C123"
    channel.name = "general"
    mock_orchestrator.chat_client.get_channels.return_value = iter([channel])
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.get("/slack/channels")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["channels"]) == 1


@patch("orchestrator_service.api.get_slack_orchestrator")
def test_get_slack_channels_error(mock_get_orch, client, mock_orchestrator):
    """Test getting Slack channels with error."""
    mock_orchestrator.chat_client.get_channels.side_effect = ValueError("Test error")
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.get("/slack/channels")
    
    assert response.status_code == 500


@patch("orchestrator_service.api.get_slack_orchestrator")
def test_send_slack_message(mock_get_orch, client, mock_orchestrator):
    """Test sending Slack message."""
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.post(
        "/slack/channels/C123/messages",
        json={"content": "Test message"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@patch("orchestrator_service.api.get_slack_orchestrator")
def test_send_slack_message_error(mock_get_orch, client, mock_orchestrator):
    """Test sending Slack message with error."""
    mock_orchestrator.chat_client.send_message.side_effect = ValueError("Test error")
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.post(
        "/slack/channels/C123/messages",
        json={"content": "Test message"},
    )
    
    assert response.status_code == 500


@patch("orchestrator_service.api.get_slack_orchestrator")
def test_get_slack_metrics(mock_get_orch, client, mock_orchestrator):
    """Test getting Slack metrics."""
    mock_get_orch.return_value = mock_orchestrator
    
    response = client.get("/slack/metrics")
    
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data


@patch("orchestrator_service.api.get_slack_orchestrator")
def test_get_slack_metrics_error(mock_get_orch, client):
    """Test getting Slack metrics with error."""
    mock_get_orch.side_effect = ValueError("Test error")
    
    response = client.get("/slack/metrics")
    
    assert response.status_code == 500

