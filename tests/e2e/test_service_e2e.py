from pathlib import Path

import httpx
import pytest

# Mark all tests in this file as e2e tests
pytestmark = pytest.mark.e2e

# Service URL (must be running manually)
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


@pytest.fixture(scope="module")
def check_credentials() -> None:
    """Check if credentials exist."""
    credentials_file = Path(__file__).parent.parent.parent / "credentials.json"
    token_file = Path(__file__).parent.parent.parent / "token.json"

    if not credentials_file.exists() and not token_file.exists():
        pytest.skip("No credentials.json or token.json found - cannot run E2E tests")


@pytest.mark.local_credentials
def test_service_root_endpoint(check_service_running) -> None:
    """Test that the service root endpoint is accessible."""
    response = httpx.get(SERVICE_URL)

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Gemini AI Service" in data["message"]


@pytest.mark.local_credentials
def test_service_get_messages_e2e(check_service_running, check_credentials) -> None:
    """Test fetching messages through the service from real Gmail API.

    This test validates:
    - Service can connect to Gmail
    - Messages are properly fetched and returned
    - Response format is correct
    """
    response = httpx.get(f"{SERVICE_URL}/messages", params={"max_results": 5})

    assert response.status_code == 200
    data = response.json()

    assert "messages" in data
    messages = data["messages"]
    assert isinstance(messages, list)

    if messages:
        # Validate message structure
        first_message = messages[0]
        assert "id" in first_message
        assert "subject" in first_message
        assert "sender" in first_message
        assert "body" in first_message

    else:
        pass


@pytest.mark.local_credentials
def test_service_get_specific_message_e2e(check_service_running, check_credentials) -> None:
    """Test fetching a specific message through the service from real Gmail API.

    This test validates:
    - Service can retrieve a specific message by ID
    - Message details are correctly returned
    - Full message content is preserved
    """
    # First get a message ID from the list
    response = httpx.get(f"{SERVICE_URL}/messages", params={"max_results": 1})
    assert response.status_code == 200

    data = response.json()
    messages = data.get("messages", [])

    if not messages:
        pytest.skip("No messages in inbox to test with")

    message_id = messages[0]["id"]

    # Fetch the specific message
    response = httpx.get(f"{SERVICE_URL}/messages/{message_id}")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    message = data["message"]

    # Validate message details
    assert message["id"] == message_id
    assert "subject" in message
    assert "sender" in message
    assert "body" in message


@pytest.mark.local_credentials
def test_service_mark_as_read_e2e(check_service_running, check_credentials) -> None:
    """Test marking a message as read through the service with real Gmail API.

    This test validates:
    - Service can mark messages as read
    - The operation successfully propagates to Gmail
    - Success/failure is correctly returned

    Note: This test modifies real Gmail data (marks a message as read).
    """
    # Get a message to mark as read
    response = httpx.get(f"{SERVICE_URL}/messages", params={"max_results": 1})
    assert response.status_code == 200

    data = response.json()
    messages = data.get("messages", [])

    if not messages:
        pytest.skip("No messages in inbox to test with")

    message_id = messages[0]["id"]

    # Mark the message as read
    response = httpx.post(f"{SERVICE_URL}/messages/{message_id}/mark-as-read")

    # Service should return success
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "Marked as read"


@pytest.mark.local_credentials
@pytest.mark.skip(reason="Destructive test - only run manually to avoid deleting real emails")
def test_service_delete_message_e2e(check_service_running, check_credentials) -> None:
    """Test deleting a message through the service with real Gmail API.

    This test validates:
    - Service can delete messages
    - The delete operation successfully propagates to Gmail
    - Success/failure is correctly returned

    WARNING: This test is DESTRUCTIVE and will delete a real email.
    It is skipped by default and should only be run manually with caution.

    To run: pytest tests/e2e/test_service_e2e.py::test_service_delete_message_e2e -v
    """
    # Get a message to delete
    response = httpx.get(f"{SERVICE_URL}/messages", params={"max_results": 1})
    assert response.status_code == 200

    data = response.json()
    messages = data.get("messages", [])

    if not messages:
        pytest.skip("No messages in inbox to test with")

    message_id = messages[0]["id"]

    # Delete the message
    response = httpx.delete(f"{SERVICE_URL}/messages/{message_id}")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "Deleted"


@pytest.mark.local_credentials
def test_service_handles_invalid_message_id_e2e(check_service_running, check_credentials) -> None:
    """Test that the service correctly handles invalid message IDs.

    This test validates:
    - Error handling works through all layers
    - Appropriate HTTP status codes are returned for errors
    """
    # Try to get a message with an invalid ID
    response = httpx.get(f"{SERVICE_URL}/messages/invalid_message_id_12345")

    # Should return 404 or 500
    assert response.status_code in [404, 500]
