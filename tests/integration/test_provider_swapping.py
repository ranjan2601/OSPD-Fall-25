"""Tests demonstrating provider swapping capability."""

import pytest
from unittest.mock import Mock, patch


# @pytest.mark.integration
# @pytest.mark.skipif(
#     sys.platform == "darwin",
#     reason="Slack import fails locally due to SQLite, will run in CI",
# )
def test_same_ai_different_chat_providers() -> None:
    """Verify Gemini AI works with both Discord and Slack."""
    from ai_chat_orchestrator.factory import (
        create_gemini_discord_orchestrator,
        create_gemini_slack_orchestrator,
    )

    test_query = "What is machine learning?"
    expected_ai_response = "Machine learning is a subset of AI"

    discord_orch = create_gemini_discord_orchestrator(gemini_api_key="test_key")

    with patch.object(discord_orch.chat_client, "get_messages") as mock_get:
        mock_message = Mock()
        mock_message.id = "msg_1"
        mock_message.content = test_query
        mock_get.return_value = [mock_message]

        with patch.object(discord_orch.ai_client, "generate_response") as mock_ai:
            mock_ai.return_value = expected_ai_response

            with patch.object(discord_orch.chat_client, "send_message") as mock_send:
                mock_send.return_value = True

                result1 = discord_orch.handle_message("channel_1", "msg_1")
                assert result1 is True
                assert mock_ai.call_args[1]["user_input"] == test_query

    slack_orch = create_gemini_slack_orchestrator(
        gemini_api_key="test_key",
        slack_token="xoxb-test",
    )

    with patch.object(slack_orch.chat_client, "get_messages") as mock_get:
        mock_message = Mock()
        mock_message.id = "1234567890.123456"
        mock_message.content = test_query
        mock_get.return_value = [mock_message]

        with patch.object(slack_orch.ai_client, "generate_response") as mock_ai:
            mock_ai.return_value = expected_ai_response

            with patch.object(slack_orch.chat_client, "send_message") as mock_send:
                mock_send.return_value = True

                result2 = slack_orch.handle_message("C123456", "1234567890.123456")
                assert result2 is True
                assert mock_ai.call_args[1]["user_input"] == test_query

    assert result1 == result2


@pytest.mark.integration
def test_provider_independence() -> None:
    """Verify changing chat provider doesn't affect AI logic."""
    from ai_chat_orchestrator import AIChatOrchestrator

    mock_ai = Mock()
    mock_ai.generate_response.return_value = "Consistent AI response"

    mock_discord = Mock()
    mock_discord_message = Mock()
    mock_discord_message.id = "msg1"
    mock_discord_message.content = "Hello"
    mock_discord.get_messages.return_value = [mock_discord_message]
    mock_discord.send_message.return_value = True

    mock_slack = Mock()
    mock_slack_message = Mock()
    mock_slack_message.id = "msg2"
    mock_slack_message.content = "Hello"
    mock_slack.get_messages.return_value = [mock_slack_message]
    mock_slack.send_message.return_value = True

    orch1 = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_discord)
    orch2 = AIChatOrchestrator(ai_client=mock_ai, chat_client=mock_slack)

    result1 = orch1.handle_message("ch1", "msg1")
    result2 = orch2.handle_message("ch2", "msg2")

    assert result1 is True
    assert result2 is True
    assert mock_ai.generate_response.call_count == 2
