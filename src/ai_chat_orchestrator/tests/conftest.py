"""Pytest fixtures for orchestrator tests."""

from typing import Any
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_ai_client() -> Any:
    """Mock AIInterface client."""
    client = Mock()
    client.generate_response.return_value = "Mock AI response"
    return client


@pytest.fixture
def mock_chat_client() -> Any:
    """Mock ChatInterface client."""
    client = Mock()

    mock_message = Mock()
    mock_message.id = "msg_123"
    mock_message.content = "Hello AI"
    mock_message.sender_id = "user_456"
    mock_message.channel_id = "channel_789"

    client.get_message.return_value = mock_message
    client.send_message.return_value = True

    return client


@pytest.fixture
def orchestrator(mock_ai_client: Any, mock_chat_client: Any) -> Any:
    """Create orchestrator with mocked clients."""
    from ai_chat_orchestrator import AIChatOrchestrator

    return AIChatOrchestrator(
        ai_client=mock_ai_client,
        chat_client=mock_chat_client,
        system_prompt="Test prompt",
    )
