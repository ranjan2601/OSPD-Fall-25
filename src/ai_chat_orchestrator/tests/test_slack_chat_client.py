"""Unit tests for SlackChatClient implementation."""

from unittest.mock import Mock, patch


def test_slack_message_adapter_id() -> None:
    """Test SlackMessageAdapter returns message ID."""
    from ai_chat_orchestrator.slack_chat_client import SlackMessageAdapter

    mock_msg = Mock()
    mock_msg.id = "msg123"
    mock_msg.ts = "1234567890.123"

    adapter = SlackMessageAdapter(mock_msg)
    assert adapter.id == "msg123"


def test_slack_message_adapter_id_uses_ts_when_no_id() -> None:
    """Test SlackMessageAdapter uses ts when id is None."""
    from ai_chat_orchestrator.slack_chat_client import SlackMessageAdapter

    mock_msg = Mock()
    mock_msg.id = None
    mock_msg.ts = "1234567890.123"

    adapter = SlackMessageAdapter(mock_msg)
    assert adapter.id == "1234567890.123"


def test_slack_message_adapter_content() -> None:
    """Test SlackMessageAdapter returns message content."""
    from ai_chat_orchestrator.slack_chat_client import SlackMessageAdapter

    mock_msg = Mock()
    mock_msg.text = "Hello from Slack"

    adapter = SlackMessageAdapter(mock_msg)
    assert adapter.content == "Hello from Slack"


def test_slack_message_adapter_sender_id() -> None:
    """Test SlackMessageAdapter returns empty sender_id."""
    from ai_chat_orchestrator.slack_chat_client import SlackMessageAdapter

    mock_msg = Mock()
    adapter = SlackMessageAdapter(mock_msg)
    assert adapter.sender_id == ""


def test_slack_chat_client_initialization() -> None:
    """Test SlackChatClient initializes with default base URL."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient") as mock_slack:
        SlackChatClient(token="xoxb-test-token")

        mock_slack.assert_called_once_with(
            base_url="https://slack.com/api",
            token="xoxb-test-token",
        )


def test_slack_chat_client_initialization_with_custom_base_url() -> None:
    """Test SlackChatClient initializes with custom base URL."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient") as mock_slack:
        SlackChatClient(base_url="https://custom.slack.com", token="xoxb-token")

        mock_slack.assert_called_once_with(
            base_url="https://custom.slack.com",
            token="xoxb-token",
        )


def test_get_messages_success() -> None:
    """Test get_messages retrieves messages successfully."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    mock_backend = Mock()
    mock_msg = Mock()
    mock_msg.id = "msg1"
    mock_msg.ts = "1234567890"
    mock_msg.text = "Test message"
    mock_backend.get_channel_history.return_value = [mock_msg]

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient", return_value=mock_backend):
        client = SlackChatClient(token="xoxb-token")
        messages = client.get_messages("C123456", limit=10)

        assert len(messages) == 1
        assert messages[0].id == "msg1"
        assert messages[0].content == "Test message"
        mock_backend.get_channel_history.assert_called_once_with("C123456", limit=10)


def test_get_messages_exception_returns_empty_list() -> None:
    """Test get_messages returns empty list on exception."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    mock_backend = Mock()
    mock_backend.get_channel_history.side_effect = RuntimeError("Slack API error")

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient", return_value=mock_backend):
        client = SlackChatClient(token="xoxb-token")
        messages = client.get_messages("C123456")

        assert messages == []


def test_send_message_success() -> None:
    """Test send_message sends successfully."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    mock_backend = Mock()
    mock_result = Mock()
    mock_result.ts = "1234567890.123"
    mock_backend.post_message.return_value = mock_result

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient", return_value=mock_backend):
        client = SlackChatClient(token="xoxb-token")
        result = client.send_message("C123456", "Hello Slack!")

        assert result is True
        mock_backend.post_message.assert_called_once_with("C123456", "Hello Slack!")


def test_send_message_returns_false_on_none_result() -> None:
    """Test send_message returns False when result is None."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    mock_backend = Mock()
    mock_backend.post_message.return_value = None

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient", return_value=mock_backend):
        client = SlackChatClient(token="xoxb-token")
        result = client.send_message("C123456", "Hello")

        assert result is False


def test_send_message_returns_false_on_empty_ts() -> None:
    """Test send_message returns False when ts is empty."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    mock_backend = Mock()
    mock_result = Mock()
    mock_result.ts = ""
    mock_backend.post_message.return_value = mock_result

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient", return_value=mock_backend):
        client = SlackChatClient(token="xoxb-token")
        result = client.send_message("C123456", "Hello")

        assert result is False


def test_send_message_exception_returns_false() -> None:
    """Test send_message returns False on exception."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    mock_backend = Mock()
    mock_backend.post_message.side_effect = RuntimeError("Slack API error")

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient", return_value=mock_backend):
        client = SlackChatClient(token="xoxb-token")
        result = client.send_message("C123456", "Hello")

        assert result is False


def test_delete_message_returns_true() -> None:
    """Test delete_message returns True (no-op implementation)."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient"):
        client = SlackChatClient(token="xoxb-token")
        result = client.delete_message("C123456", "msg123")

        assert result is True


def test_close_calls_backend_close() -> None:
    """Test close calls backend close method if it exists."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    mock_backend = Mock()
    mock_backend.close = Mock()

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient", return_value=mock_backend):
        client = SlackChatClient(token="xoxb-token")
        client.close()

        mock_backend.close.assert_called_once()


def test_close_handles_no_close_method() -> None:
    """Test close handles backend without close method."""
    from ai_chat_orchestrator.slack_chat_client import SlackChatClient

    mock_backend = Mock(spec=[])  # No close method

    with patch("ai_chat_orchestrator.slack_chat_client.SlackClient", return_value=mock_backend):
        client = SlackChatClient(token="xoxb-token")
        # Should not raise exception
        client.close()
