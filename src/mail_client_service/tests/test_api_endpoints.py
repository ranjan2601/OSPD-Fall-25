"""Unit tests for FastAPI endpoints using dependency injection."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from mail_client_api import Client
from mail_client_service.api import get_mail_client
from mail_client_service.main import app


@pytest.fixture
def mock_client():
    """Create a mock mail client for testing."""
    mock = MagicMock(spec=Client)

    # Create a mock message
    mock_message = MagicMock()
    mock_message.id = "m1"
    mock_message.subject = "Test Subject"
    mock_message.from_ = "sender@example.com"
    mock_message.body = "Test body"

    # Configure default behaviors
    mock.get_messages.return_value = [mock_message]
    mock.get_message.return_value = mock_message
    mock.delete_message.return_value = True
    mock.mark_as_read.return_value = True

    return mock


@pytest.fixture
def test_client(mock_client):
    """Create a test client with mocked dependencies."""
    # Override the dependency
    app.dependency_overrides[get_mail_client] = lambda: mock_client

    # Create test client
    client = TestClient(app)

    yield client

    # Clean up
    app.dependency_overrides.clear()


# GET /messages tests
def test_get_messages_success(test_client, mock_client):
    """Test successful retrieval of messages."""
    # Act
    response = test_client.get("/messages")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    assert len(data["messages"]) == 1
    assert data["messages"][0]["id"] == "m1"
    assert data["messages"][0]["subject"] == "Test Subject"
    assert data["messages"][0]["sender"] == "sender@example.com"
    assert data["messages"][0]["body"] == "Test body"

    # Verify mock was called
    mock_client.get_messages.assert_called_once()


def test_get_messages_empty(test_client, mock_client):
    """Test retrieval when no messages exist."""
    # Arrange
    mock_client.get_messages.return_value = []

    # Act
    response = test_client.get("/messages")

    # Assert
    assert response.status_code == 200
    assert response.json()["messages"] == []


def test_get_messages_500(test_client, mock_client):
    """Test error handling when client raises exception."""
    # Arrange
    mock_client.get_messages.side_effect = Exception("Database error")

    # Act
    response = test_client.get("/messages")

    # Assert
    assert response.status_code == 500
    assert "Error fetching messages" in response.json()["detail"]


# GET /messages/{message_id} tests
def test_get_message_ok(test_client, mock_client):
    """Test successful retrieval of a single message."""
    # Act
    response = test_client.get("/messages/m1")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"]["id"] == "m1"
    assert data["message"]["subject"] == "Test Subject"

    # Verify mock was called with correct parameter
    mock_client.get_message.assert_called_once_with("m1")


def test_get_message_not_found(test_client, mock_client):
    """Test 404 when message doesn't exist."""
    # Arrange
    mock_client.get_message.side_effect = KeyError("Message not found")

    # Act
    response = test_client.get("/messages/nonexistent")

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_message_500(test_client, mock_client):
    """Test error handling for unexpected exceptions."""
    # Arrange
    mock_client.get_message.side_effect = Exception("Unexpected error")

    # Act
    response = test_client.get("/messages/m1")

    # Assert
    assert response.status_code == 500


# DELETE /messages/{message_id} tests
def test_delete_message_ok(test_client, mock_client):
    """Test successful deletion of a message."""
    # Act
    response = test_client.delete("/messages/m1")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["message_id"] == "m1"
    assert data["status"] == "Deleted"

    # Verify mock was called
    mock_client.delete_message.assert_called_once_with("m1")


def test_delete_message_not_found(test_client, mock_client):
    """Test 404 when trying to delete non-existent message."""
    # Arrange
    mock_client.delete_message.side_effect = KeyError("Message not found")

    # Act
    response = test_client.delete("/messages/nonexistent")

    # Assert
    assert response.status_code == 404


def test_delete_message_failed_returns_500(test_client, mock_client):
    """Test 500 when deletion fails."""
    # Arrange
    mock_client.delete_message.return_value = False

    # Act
    response = test_client.delete("/messages/m1")

    # Assert
    assert response.status_code == 500
    assert "Failed to delete" in response.json()["detail"]


def test_delete_message_500(test_client, mock_client):
    """Test error handling for unexpected exceptions."""
    # Arrange
    mock_client.delete_message.side_effect = Exception("Unexpected error")

    # Act
    response = test_client.delete("/messages/m1")

    # Assert
    assert response.status_code == 500


# POST /messages/{message_id}/mark-as-read tests
def test_mark_as_read_ok(test_client, mock_client):
    """Test successful marking of message as read."""
    # Act
    response = test_client.post("/messages/m1/mark-as-read")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["message_id"] == "m1"
    assert data["status"] == "Marked as read"

    # Verify mock was called
    mock_client.mark_as_read.assert_called_once_with("m1")


def test_mark_as_read_not_found(test_client, mock_client):
    """Test 404 when message doesn't exist."""
    # Arrange
    mock_client.mark_as_read.side_effect = KeyError("Message not found")

    # Act
    response = test_client.post("/messages/nonexistent/mark-as-read")

    # Assert
    assert response.status_code == 404


def test_mark_as_read_failed_returns_500(test_client, mock_client):
    """Test 500 when marking as read fails."""
    # Arrange
    mock_client.mark_as_read.return_value = False

    # Act
    response = test_client.post("/messages/m1/mark-as-read")

    # Assert
    assert response.status_code == 500
    assert "Failed to mark" in response.json()["detail"]


def test_mark_as_read_500(test_client, mock_client):
    """Test error handling for unexpected exceptions."""
    # Arrange
    mock_client.mark_as_read.side_effect = Exception("Unexpected error")

    # Act
    response = test_client.post("/messages/m1/mark-as-read")

    # Assert
    assert response.status_code == 500


# Root endpoint test
def test_root_endpoint(test_client):
    """Test the root health check endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Mail Client Service is running"}


# Dependency injection tests
def test_get_mail_client_with_real_credentials():
    """Test get_mail_client when real credentials are available."""
    from unittest.mock import patch

    # Mock get_client where it's used in api.py
    mock_client = MagicMock(spec=Client)
    with patch("mail_client_service.api.mail_client_api.get_client", return_value=mock_client):
        client = get_mail_client()
        assert client is mock_client


def test_get_mail_client_falls_back_to_mock():
    """Test get_mail_client falls back to mock when no credentials."""
    from unittest.mock import patch

    # Mock get_client to raise RuntimeError with credentials message
    with patch(
        "mail_client_service.api.mail_client_api.get_client",
        side_effect=RuntimeError("No valid credentials found"),
    ):
        client = get_mail_client()
        # Should return a mock client
        assert client is not None
        # Verify it has the expected methods
        assert hasattr(client, "get_messages")
        assert hasattr(client, "get_message")
        assert hasattr(client, "delete_message")
        assert hasattr(client, "mark_as_read")


def test_get_mail_client_propagates_other_runtime_errors():
    """Test get_mail_client propagates RuntimeErrors that are not credential-related."""
    from unittest.mock import patch

    # Mock get_client to raise a different RuntimeError
    with (
        patch(
            "mail_client_service.api.mail_client_api.get_client",
            side_effect=RuntimeError("Database connection failed"),
        ),
        pytest.raises(RuntimeError, match="Database connection failed"),
    ):
        get_mail_client()


def test_mock_client_get_messages():
    """Test the mock client's get_messages functionality."""
    from unittest.mock import patch

    # Get the mock client
    with patch(
        "mail_client_service.api.mail_client_api.get_client",
        side_effect=RuntimeError("No valid credentials found"),
    ):
        client = get_mail_client()
        messages = list(client.get_messages(max_results=2))

        # Should return mock messages
        assert len(messages) <= 3  # Mock has 3 messages
        assert all(hasattr(msg, "id") for msg in messages)
        assert all(hasattr(msg, "subject") for msg in messages)


def test_mock_client_get_message():
    """Test the mock client's get_message functionality."""
    from unittest.mock import patch

    # Get the mock client
    with patch(
        "mail_client_service.api.mail_client_api.get_client",
        side_effect=RuntimeError("No valid credentials found"),
    ):
        client = get_mail_client()
        message = client.get_message("1")

        # Should return a mock message
        assert message.id == "1"
        assert hasattr(message, "subject")


def test_mock_client_delete_message():
    """Test the mock client's delete_message functionality."""
    from unittest.mock import patch

    # Get the mock client
    with patch(
        "mail_client_service.api.mail_client_api.get_client",
        side_effect=RuntimeError("No valid credentials found"),
    ):
        client = get_mail_client()
        result = client.delete_message("1")

        # Should succeed
        assert result is True


def test_mock_client_mark_as_read():
    """Test the mock client's mark_as_read functionality."""
    from unittest.mock import patch

    # Get the mock client
    with patch(
        "mail_client_service.api.mail_client_api.get_client",
        side_effect=RuntimeError("No valid credentials found"),
    ):
        client = get_mail_client()
        result = client.mark_as_read("1")

        # Should succeed
        assert result is True
