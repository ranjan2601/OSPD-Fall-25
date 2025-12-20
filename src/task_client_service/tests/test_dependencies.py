"""Tests for task_client_service dependencies module."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from task_client_service.dependencies import get_task_client


@pytest.fixture
def mock_request() -> Any:
    """Create a mock FastAPI request."""
    request = MagicMock()
    request.session = {}
    request.app.state = MagicMock()
    request.url.scheme = "http"
    request.url.netloc = "localhost:8001"
    return request


def test_get_task_client_no_credentials_interactive_success(mock_request: Any) -> None:
    """Test get_task_client when no credentials, interactive auth succeeds."""
    mock_client = MagicMock()

    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        # First call raises RuntimeError (no credentials)
        # Second call with interactive=True succeeds
        mock_get_client.side_effect = [
            RuntimeError("Failed to obtain credentials"),
            mock_client,
        ]

        result = get_task_client(mock_request)

        assert result == mock_client
        # Verify get_client was called twice: first with interactive=False, then True
        assert mock_get_client.call_count == 2
        mock_get_client.assert_any_call(interactive=False)
        mock_get_client.assert_any_call(interactive=True)


def test_get_task_client_no_credentials_interactive_runtime_error(mock_request: Any) -> None:
    """Test get_task_client when interactive auth fails with RuntimeError."""
    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        # First call raises RuntimeError (no credentials)
        # Second call also raises RuntimeError
        mock_get_client.side_effect = [
            RuntimeError("Failed to obtain credentials"),
            RuntimeError("Interactive auth failed"),
        ]

        with pytest.raises(HTTPException) as exc_info:
            get_task_client(mock_request)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail
        assert "OAuth flow should have been initiated" in exc_info.value.detail


def test_get_task_client_no_credentials_interactive_unexpected_error(mock_request: Any) -> None:
    """Test get_task_client when interactive auth fails with unexpected error."""
    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        # First call raises RuntimeError (no credentials)
        # Second call raises unexpected exception
        mock_get_client.side_effect = [
            RuntimeError("Failed to obtain credentials"),
            ValueError("Unexpected error"),
        ]

        with pytest.raises(HTTPException) as exc_info:
            get_task_client(mock_request)

        assert exc_info.value.status_code == 503
        assert "Failed to initialize task client" in exc_info.value.detail


def test_get_task_client_other_runtime_error(mock_request: Any) -> None:
    """Test get_task_client with RuntimeError not related to credentials."""
    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        # Raise RuntimeError without "credentials" in message
        mock_get_client.side_effect = RuntimeError("Some other error")

        with pytest.raises(HTTPException) as exc_info:
            get_task_client(mock_request)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail
        # Should only try once since error doesn't mention credentials
        assert mock_get_client.call_count == 1


def test_get_task_client_unexpected_exception(mock_request: Any) -> None:
    """Test get_task_client with unexpected exception type."""
    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        # Raise unexpected exception
        mock_get_client.side_effect = ValueError("Something went wrong")

        with pytest.raises(HTTPException) as exc_info:
            get_task_client(mock_request)

        assert exc_info.value.status_code == 503
        assert "Task client not available" in exc_info.value.detail


def test_get_task_client_with_valid_session_credentials(mock_request: Any) -> None:
    """Test get_task_client with valid credentials in session."""
    mock_client = MagicMock()
    creds = {"token": "test_token", "refresh_token": "test_refresh"}
    mock_request.session["credentials"] = json.dumps(creds)

    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        mock_get_client.return_value = mock_client

        result = get_task_client(mock_request)

        assert result == mock_client
        # Should have set app.state.current_session_creds
        assert mock_request.app.state.current_session_creds == creds
        # Should only call get_client once with interactive=False
        mock_get_client.assert_called_once_with(interactive=False)


def test_get_task_client_with_invalid_json_in_session(mock_request: Any) -> None:
    """Test get_task_client with invalid JSON in session."""
    mock_client = MagicMock()
    mock_request.session["credentials"] = "not-valid-json{["

    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        mock_get_client.return_value = mock_client

        # Should still succeed but with None for session_creds
        result = get_task_client(mock_request)

        assert result == mock_client
        # current_session_creds should be None due to parse error
        assert mock_request.app.state.current_session_creds is None


def test_get_task_client_sets_environment_base_url(mock_request: Any) -> None:
    """Test that get_task_client sets TASK_SERVICE_BASE_URL environment variable."""
    mock_client = MagicMock()
    mock_request.url.scheme = "https"
    mock_request.url.netloc = "example.com:443"

    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        mock_get_client.return_value = mock_client

        with patch("task_client_service.dependencies.os") as mock_os:
            mock_os.environ = {}

            get_task_client(mock_request)

            # Verify environment variable was set
            assert mock_os.environ["TASK_SERVICE_BASE_URL"] == "https://example.com:443"


def test_get_task_client_no_session_keys_method(mock_request: Any) -> None:
    """Test get_task_client when session doesn't have keys() method."""
    mock_client = MagicMock()
    # Create a session object without keys() method but with get() method
    mock_session = MagicMock()
    del mock_session.keys  # Remove keys method
    mock_session.get.return_value = None
    mock_request.session = mock_session

    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        mock_get_client.return_value = mock_client

        # Should handle gracefully and still work
        result = get_task_client(mock_request)

        assert result == mock_client


def test_get_task_client_sets_context_var(mock_request: Any) -> None:
    """Test that get_task_client sets the current_request context variable."""
    mock_client = MagicMock()

    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        mock_get_client.return_value = mock_client

        with patch("task_client_service.dependencies.current_request") as mock_context_var:
            get_task_client(mock_request)

            # Verify context var was set
            mock_context_var.set.assert_called_once_with(mock_request)


def test_get_task_client_credentials_error_with_lowercase(mock_request: Any) -> None:
    """Test error message detection is case-insensitive for 'credentials'."""
    mock_client = MagicMock()

    with patch("task_client_service.dependencies.get_client") as mock_get_client:
        # Error message with lowercase "credentials"
        mock_get_client.side_effect = [
            RuntimeError("No valid CREDENTIALS found"),
            mock_client,
        ]

        result = get_task_client(mock_request)

        assert result == mock_client
        # Should have triggered interactive flow
        assert mock_get_client.call_count == 2
