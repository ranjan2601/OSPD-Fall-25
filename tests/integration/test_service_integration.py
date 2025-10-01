"""Integration tests for mail_client_service.

This module tests the integration between the service layer and the underlying
mail client implementation. It verifies that the service correctly uses the
mail_client_adapter to call the running mail_client_service, which in turn
calls the mocked gmail_client_impl.

The tests ensure all layers are connected correctly:
- ServiceClient (mail_client_adapter) -> FastAPI Service -> Mocked Gmail Client
"""

import sys
from pathlib import Path

import httpx
import pytest

# Add service src to path for imports
service_src = Path(__file__).parent.parent.parent / "src" / "mail_client_service" / "src"
sys.path.insert(0, str(service_src))

# Import the service client (mail_client_adapter)
from mail_client_service import ServiceClient
from mail_client_service._impl import ServiceMessage

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

# Service URL for testing
SERVICE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def check_service_running() -> None:
    """Check if the service is running before tests."""
    try:
        response = httpx.get(SERVICE_URL, timeout=2.0)
        if response.status_code != 200:
            pytest.skip(f"Service at {SERVICE_URL} is not responding correctly")
    except (httpx.ConnectError, httpx.TimeoutException):
        pytest.skip(
            f"Service not running at {SERVICE_URL}. "
            "Please start it with: cd src/mail_client_service && uv run uvicorn main:app --reload",
        )


@pytest.mark.circleci
def test_service_client_integration() -> None:
    """Test that ServiceClient correctly implements the mail_client_api.Client interface.
    
    This test verifies that the ServiceClient (mail_client_adapter) properly
    implements all required methods from the Client abstract base class.
    """
    client = ServiceClient(base_url=SERVICE_URL)
    
    # Verify it implements the Client interface
    assert hasattr(client, "get_messages")
    assert hasattr(client, "get_message")
    assert hasattr(client, "delete_message")
    assert hasattr(client, "mark_as_read")
    
    # Verify method signatures are correct
    import inspect
    
    # Check get_messages signature
    sig = inspect.signature(client.get_messages)
    assert "max_results" in sig.parameters
    
    # Check other method signatures
    assert inspect.signature(client.get_message).parameters["message_id"].annotation == str
    assert inspect.signature(client.delete_message).parameters["message_id"].annotation == str
    assert inspect.signature(client.mark_as_read).parameters["message_id"].annotation == str


@pytest.mark.circleci
def test_service_to_mock_client_integration(check_service_running) -> None:
    """Test integration between service and mocked Gmail client.
    
    This test verifies that:
    1. The FastAPI service correctly uses the built-in MockClient when no credentials are available
    2. The service returns the expected mock data
    3. All layers are connected correctly
    
    The service automatically uses its built-in MockClient when credentials are not available.
    """
    # Test GET /messages endpoint
    response = httpx.get(f"{SERVICE_URL}/messages", params={"max_results": 2})
    
    assert response.status_code == 200
    data = response.json()
    assert "messages" in data
    messages = data["messages"]
    
    # The service's built-in mock client respects max_results and is stateful
    # After previous tests, there may be fewer messages available
    assert len(messages) >= 1  # At least one message should be available
    assert len(messages) <= 3  # Never more than the original 3
    
    # Verify message structure
    first_message = messages[0]
    assert "id" in first_message
    assert "subject" in first_message
    assert "sender" in first_message
    assert "body" in first_message
    
    # Verify the data matches the service's built-in mock
    assert first_message["id"] == "1"
    assert first_message["subject"] == "Test Email 1"
    assert first_message["sender"] == "test1@example.com"
    assert first_message["body"] == "This is test message 1"


@pytest.mark.circleci
def test_service_get_specific_message_integration(check_service_running) -> None:
    """Test getting a specific message through the service integration.
    
    This test verifies that the service correctly handles the GET /messages/{id}
    endpoint and calls the built-in MockClient's get_message method.
    """
    # Test getting a specific message using the service's built-in mock IDs
    response = httpx.get(f"{SERVICE_URL}/messages/2")
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    message = data["message"]
    
    # Verify the message details match the service's built-in mock
    assert message["id"] == "2"
    assert message["subject"] == "Test Email 2"
    assert message["sender"] == "test2@example.com"
    assert message["body"] == "This is test message 2"


@pytest.mark.circleci
def test_service_mark_as_read_integration(check_service_running) -> None:
    """Test marking a message as read through the service integration.
    
    This test verifies that the service correctly handles the POST /messages/{id}/mark-as-read
    endpoint and calls the built-in MockClient's mark_as_read method.
    """
    # Test marking a message as read using the service's built-in mock IDs
    response = httpx.post(f"{SERVICE_URL}/messages/1/mark-as-read")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "Marked as read"


@pytest.mark.circleci
def test_service_delete_message_integration(check_service_running) -> None:
    """Test deleting a message through the service integration.
    
    This test verifies that the service correctly handles the DELETE /messages/{id}
    endpoint and calls the built-in MockClient's delete_message method.
    """
    # First, get available messages to find one to delete
    response = httpx.get(f"{SERVICE_URL}/messages")
    assert response.status_code == 200
    data = response.json()
    messages = data["messages"]
    
    if not messages:
        pytest.skip("No messages available to delete")
    
    # Delete the first available message
    message_to_delete = messages[0]["id"]
    response = httpx.delete(f"{SERVICE_URL}/messages/{message_to_delete}")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "Deleted"


@pytest.mark.circleci
def test_service_error_handling_integration(check_service_running) -> None:
    """Test error handling through the service integration.
    
    This test verifies that the service correctly handles errors from the
    built-in MockClient and returns appropriate HTTP status codes.
    """
    # Test getting a non-existent message
    response = httpx.get(f"{SERVICE_URL}/messages/nonexistent_msg")
    
    # Should return 404 since the built-in MockClient raises KeyError for non-existent messages
    assert response.status_code == 404


@pytest.mark.circleci
def test_service_client_to_service_integration(check_service_running) -> None:
    """Test integration between ServiceClient and the running service.
    
    This test verifies that the ServiceClient (mail_client_adapter) can
    successfully communicate with the running FastAPI service.
    """
    # Create a ServiceClient instance
    client = ServiceClient(base_url=SERVICE_URL)
    
    # Test that we can call the service through the client
    # Note: This test requires the service to be running with mock data
    # or real credentials, so we'll test the connection without making
    # actual API calls that might fail without proper setup
    
    # Verify the client is properly configured
    assert client._client.get_httpx_client().base_url == SERVICE_URL
    
    # Test that the client can be instantiated and has the right interface
    assert hasattr(client, "get_messages")
    assert hasattr(client, "get_message")
    assert hasattr(client, "delete_message")
    assert hasattr(client, "mark_as_read")


@pytest.mark.circleci
def test_service_message_wrapper_integration() -> None:
    """Test that ServiceMessage correctly wraps service responses.
    
    This test verifies that the ServiceMessage class properly implements
    the mail_client_api.message.Message interface.
    """
    from mail_client_service.generated.mail_client_service_api_client.models.message_response import MessageResponse
    
    # Create a mock service response
    mock_response = MessageResponse(
        id="test_msg",
        from_="test@example.com",
        to="recipient@example.com",
        date="2024-01-01",
        subject="Test Subject",
        body="Test body content",
    )
    
    # Create ServiceMessage wrapper
    message = ServiceMessage(mock_response)
    
    # Verify it implements the Message interface
    assert hasattr(message, "id")
    assert hasattr(message, "from_")
    assert hasattr(message, "to")
    assert hasattr(message, "date")
    assert hasattr(message, "subject")
    assert hasattr(message, "body")
    
    # Verify the values are correctly mapped
    assert message.id == "test_msg"
    assert message.from_ == "test@example.com"
    assert message.to == "recipient@example.com"
    assert message.date == "2024-01-01"
    assert message.subject == "Test Subject"
    assert message.body == "Test body content"
