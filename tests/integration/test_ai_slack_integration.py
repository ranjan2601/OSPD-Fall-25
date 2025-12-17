"""Integration tests for Gemini AI with Slack chat."""

import pytest
from unittest.mock import Mock, patch


# pytestmark = pytest.mark.skipif(
#     sys.platform == "darwin",
#     reason="Slack tests skip locally due to SQLite dependency, will run in CI",
# )


@pytest.mark.integration
def test_gemini_slack_orchestrator_creation() -> None:
    """Test creating orchestrator with Gemini and Slack."""
    from ai_chat_orchestrator.factory import create_gemini_slack_orchestrator

    orchestrator = create_gemini_slack_orchestrator(
        gemini_api_key="test_key",
        slack_token="xoxb-test-token",
    )

    assert orchestrator is not None
    assert orchestrator.ai_client is not None
    assert orchestrator.chat_client is not None


@pytest.mark.integration
def test_gemini_slack_message_flow() -> None:
    """Test complete message flow through Slack and Gemini."""
    from ai_chat_orchestrator.factory import create_gemini_slack_orchestrator

    orchestrator = create_gemini_slack_orchestrator(
        gemini_api_key="test_key",
        slack_token="xoxb-test-token",
    )

    with patch.object(orchestrator.chat_client, "get_messages") as mock_get:
        mock_message = Mock()
        mock_message.id = "1234567890.123456"
        mock_message.content = "Tell me a joke"
        mock_get.return_value = [mock_message]

        with patch.object(orchestrator.ai_client, "generate_response") as mock_ai:
            mock_ai.return_value = "Why did the chicken cross the road?"

            with patch.object(orchestrator.chat_client, "send_message") as mock_send:
                mock_send.return_value = True

                result = orchestrator.handle_message("C123456", "1234567890.123456")

                assert result is True
                mock_get.assert_called_once()
                mock_ai.assert_called_once()
                mock_send.assert_called_once()


@pytest.mark.integration
def test_gemini_slack_error_handling() -> None:
    """Test Slack-specific error handling."""
    from ai_chat_orchestrator.factory import create_gemini_slack_orchestrator

    orchestrator = create_gemini_slack_orchestrator(
        gemini_api_key="test_key",
        slack_token="xoxb-test",
    )

    with patch.object(orchestrator.chat_client, "get_messages") as mock_get:
        mock_get.side_effect = Exception("Slack API error")

        result = orchestrator.handle_message("C123456", "1234567890.123456")

        assert result is False
