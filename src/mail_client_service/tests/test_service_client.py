"""Unit tests for ServiceClient implementation."""

from unittest.mock import Mock, patch

import pytest

from mail_client_service import ServiceClient
from mail_client_service._impl import ServiceMessage
from mail_client_service.generated.mail_client_service_api_client.models.delete_response import DeleteResponse
from mail_client_service.generated.mail_client_service_api_client.models.mark_read_response import MarkReadResponse
from mail_client_service.generated.mail_client_service_api_client.models.message_response import MessageResponse


class TestServiceMessage:
    """Tests for ServiceMessage class."""
    
    def test_service_message_properties(self) -> None:
        """Test that ServiceMessage correctly exposes message properties."""
        response = MessageResponse(
            id="test_id",
            from_="sender@example.com",
            to="recipient@example.com", 
            date="2024-01-01",
            subject="Test Subject",
            body="Test body content"
        )
        
        message = ServiceMessage(response)
        
        assert message.id == "test_id"
        assert message.from_ == "sender@example.com"
        assert message.to == "recipient@example.com"
        assert message.date == "2024-01-01"
        assert message.subject == "Test Subject"
        assert message.body == "Test body content"


class TestServiceClient:
    """Tests for ServiceClient class."""
    
    def test_init(self) -> None:
        """Test ServiceClient initialization."""
        client = ServiceClient("http://test:8080")
        assert client._client.get_httpx_client().base_url == "http://test:8080"
    
    @patch("mail_client_service._impl.get_message_messages_message_id_get")
    def test_get_message_success(self, mock_get_message: Mock) -> None:
        """Test successful message retrieval."""
        mock_response = MessageResponse(
            id="msg_123",
            from_="test@example.com",
            to="user@example.com",
            date="2024-01-01",
            subject="Test Message",
            body="Test content"
        )
        mock_get_message.sync.return_value = mock_response
        
        client = ServiceClient()
        message = client.get_message("msg_123")
        
        assert message.id == "msg_123"
        assert message.from_ == "test@example.com"
        assert message.subject == "Test Message"
        mock_get_message.sync.assert_called_once()
    
    @patch("mail_client_service._impl.get_message_messages_message_id_get")
    def test_get_message_not_found(self, mock_get_message: Mock) -> None:
        """Test message not found scenario."""
        mock_get_message.sync.return_value = None
        
        client = ServiceClient()
        
        with pytest.raises(ValueError, match="Message msg_404 not found"):
            client.get_message("msg_404")
    
    @patch("mail_client_service._impl.delete_message_messages_message_id_delete")
    def test_delete_message_success(self, mock_delete: Mock) -> None:
        """Test successful message deletion."""
        mock_delete.sync.return_value = DeleteResponse(success=True)
        
        client = ServiceClient()
        result = client.delete_message("msg_123")
        
        assert result is True
        mock_delete.sync.assert_called_once()
    
    @patch("mail_client_service._impl.delete_message_messages_message_id_delete")
    def test_delete_message_failure(self, mock_delete: Mock) -> None:
        """Test failed message deletion."""
        mock_delete.sync.return_value = DeleteResponse(success=False)
        
        client = ServiceClient()
        result = client.delete_message("msg_123")
        
        assert result is False
    
    @patch("mail_client_service._impl.delete_message_messages_message_id_delete")
    def test_delete_message_none_response(self, mock_delete: Mock) -> None:
        """Test message deletion with None response."""
        mock_delete.sync.return_value = None
        
        client = ServiceClient()
        result = client.delete_message("msg_123")
        
        assert result is False
    
    @patch("mail_client_service._impl.mark_as_read_messages_message_id_read_put")
    def test_mark_as_read_success(self, mock_mark_read: Mock) -> None:
        """Test successful mark as read."""
        mock_mark_read.sync.return_value = MarkReadResponse(success=True)
        
        client = ServiceClient()
        result = client.mark_as_read("msg_123")
        
        assert result is True
        mock_mark_read.sync.assert_called_once()
    
    @patch("mail_client_service._impl.mark_as_read_messages_message_id_read_put")
    def test_mark_as_read_failure(self, mock_mark_read: Mock) -> None:
        """Test failed mark as read."""
        mock_mark_read.sync.return_value = MarkReadResponse(success=False)
        
        client = ServiceClient()
        result = client.mark_as_read("msg_123")
        
        assert result is False
    
    @patch("mail_client_service._impl.get_messages_messages_get")
    def test_get_messages_success(self, mock_get_messages: Mock) -> None:
        """Test successful messages retrieval."""
        mock_responses = [
            MessageResponse(
                id="msg_1",
                from_="sender1@example.com",
                to="user@example.com",
                date="2024-01-01",
                subject="Message 1",
                body="Content 1"
            ),
            MessageResponse(
                id="msg_2", 
                from_="sender2@example.com",
                to="user@example.com",
                date="2024-01-02",
                subject="Message 2",
                body="Content 2"
            )
        ]
        mock_get_messages.sync.return_value = mock_responses
        
        client = ServiceClient()
        messages = list(client.get_messages(max_results=2))
        
        assert len(messages) == 2
        assert messages[0].id == "msg_1"
        assert messages[1].id == "msg_2"
        mock_get_messages.sync.assert_called_once_with(client=client._client, max_results=2)
    
    @patch("mail_client_service._impl.get_messages_messages_get")
    def test_get_messages_empty(self, mock_get_messages: Mock) -> None:
        """Test empty messages response."""
        mock_get_messages.sync.return_value = None
        
        client = ServiceClient()
        messages = list(client.get_messages())
        
        assert len(messages) == 0
    
    @patch("mail_client_service._impl.get_messages_messages_get")
    def test_get_messages_default_limit(self, mock_get_messages: Mock) -> None:
        """Test get_messages with default limit."""
        mock_get_messages.sync.return_value = []
        
        client = ServiceClient()
        list(client.get_messages())
        
        mock_get_messages.sync.assert_called_once_with(client=client._client, max_results=10)
