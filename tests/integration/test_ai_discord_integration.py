"""Integration tests for Gemini AI with Discord chat."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.integration
def test_gemini_discord_registration() -> None:
    """Test that Gemini and Discord can be registered."""
    import ai_client_api
    import chat_client_api
    import discord_client_impl
    import gemini_client_impl

    gemini_client_impl.register()
    discord_client_impl.register()

    assert callable(ai_client_api.get_client)
    assert callable(chat_client_api.get_client)


@pytest.mark.integration
def test_gemini_discord_orchestrator_creation() -> None:
    """Test creating orchestrator with Gemini and Discord."""
    from ai_chat_orchestrator.factory import create_gemini_discord_orchestrator

    orchestrator = create_gemini_discord_orchestrator(
        gemini_api_key="test_key",
        discord_user_id=None,
    )

    assert orchestrator is not None
    assert orchestrator.ai_client is not None
    assert orchestrator.chat_client is not None


@pytest.mark.integration
def test_gemini_discord_message_flow() -> None:
    """Test complete message flow through Discord and Gemini."""
    from ai_chat_orchestrator.factory import create_gemini_discord_orchestrator

    orchestrator = create_gemini_discord_orchestrator(gemini_api_key="test_key")

    with patch.object(orchestrator.chat_client, "get_message") as mock_get:
        mock_message = Mock()
        mock_message.content = "What is the capital of France?"
        mock_get.return_value = mock_message

        with patch.object(orchestrator.ai_client, "generate_response") as mock_ai:
            mock_ai.return_value = "The capital of France is Paris."

            with patch.object(orchestrator.chat_client, "send_message") as mock_send:
                mock_send.return_value = True

                result = orchestrator.handle_message("channel_456", "msg_123")

                assert result is True
                mock_get.assert_called_once_with("channel_456", "msg_123")
                mock_ai.assert_called_once()
                assert mock_ai.call_args[1]["user_input"] == "What is the capital of France?"
                mock_send.assert_called_once()
                assert "Paris" in mock_send.call_args[0][1]


@pytest.mark.integration
def test_gemini_discord_ai_error_handling() -> None:
    """Test error handling when Gemini API fails."""
    from ai_chat_orchestrator.factory import create_gemini_discord_orchestrator

    orchestrator = create_gemini_discord_orchestrator(gemini_api_key="test_key")

    with patch.object(orchestrator.chat_client, "get_message") as mock_get:
        mock_message = Mock()
        mock_message.content = "Test message"
        mock_get.return_value = mock_message

        with patch.object(orchestrator.ai_client, "generate_response") as mock_ai:
            mock_ai.side_effect = RuntimeError("Gemini API error")

            result = orchestrator.handle_message("channel_1", "msg_1")

            assert result is False


@pytest.mark.integration
def test_gemini_discord_chat_error_handling() -> None:
    """Test error handling when Discord send fails."""
    from ai_chat_orchestrator.factory import create_gemini_discord_orchestrator

    orchestrator = create_gemini_discord_orchestrator(gemini_api_key="test_key")

    with patch.object(orchestrator.chat_client, "get_message") as mock_get:
        mock_message = Mock()
        mock_message.content = "Test message"
        mock_get.return_value = mock_message

        with patch.object(orchestrator.ai_client, "generate_response") as mock_ai:
            mock_ai.return_value = "AI response"

            with patch.object(orchestrator.chat_client, "send_message") as mock_send:
                mock_send.return_value = False

                result = orchestrator.handle_message("channel_1", "msg_1")

                assert result is False
