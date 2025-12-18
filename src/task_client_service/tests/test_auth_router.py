"""Tests for task_client_service auth router endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from task_client_service.routers.auth_router import (
    credentials_to_dict,
    get_base_url,
    get_credentials_path,
    get_redirect_uri,
)


def test_get_base_url_with_oauth_redirect_uri() -> None:
    """Test get_base_url with OAUTH_REDIRECT_URI environment variable."""
    import os

    with patch.dict(
        os.environ, {"OAUTH_REDIRECT_URI": "https://example.com/auth/callback"}, clear=False
    ):
        result = get_base_url()
        assert result == "https://example.com"


def test_get_base_url_with_oauth_redirect_uri_no_callback() -> None:
    """Test get_base_url with OAUTH_REDIRECT_URI without /auth/callback."""
    import os

    with patch.dict(os.environ, {"OAUTH_REDIRECT_URI": "https://example.com"}, clear=False):
        result = get_base_url()
        assert result == "https://example.com"


def test_get_base_url_with_render_external_url() -> None:
    """Test get_base_url with RENDER_EXTERNAL_URL environment variable."""
    with patch("task_client_service.routers.auth_router.os") as mock_os:
        mock_os.environ.get.side_effect = lambda key: {
            "RENDER_EXTERNAL_URL": "https://myapp.onrender.com/"
        }.get(key)

        result = get_base_url()

        assert result == "https://myapp.onrender.com"


def test_get_base_url_default_localhost() -> None:
    """Test get_base_url returns localhost by default."""
    with patch("task_client_service.routers.auth_router.os") as mock_os:
        mock_os.environ.get.return_value = None

        result = get_base_url()

        assert result == "http://127.0.0.1:8001"


def test_get_redirect_uri() -> None:
    """Test get_redirect_uri constructs correct URI."""
    with patch("task_client_service.routers.auth_router.get_base_url") as mock_get_base:
        mock_get_base.return_value = "https://example.com"

        result = get_redirect_uri()

        assert result == "https://example.com/auth/callback"


def test_get_credentials_path_exists() -> None:
    """Test get_credentials_path when file exists."""
    with patch("task_client_service.routers.auth_router.Path") as mock_path_class:
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path

        result = get_credentials_path()

        assert result == mock_path


def test_get_credentials_path_not_exists() -> None:
    """Test get_credentials_path when file doesn't exist."""
    with patch("task_client_service.routers.auth_router.Path") as mock_path_class:
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_path_class.return_value = mock_path

        with pytest.raises(HTTPException) as exc_info:
            get_credentials_path()

        assert exc_info.value.status_code == 500
        assert "not found" in exc_info.value.detail


def test_credentials_to_dict() -> None:
    """Test credentials_to_dict converts Credentials to dict."""
    mock_creds = MagicMock()
    mock_creds.token = "test_token"
    mock_creds.refresh_token = "test_refresh"
    mock_creds.token_uri = "https://oauth2.googleapis.com/token"
    mock_creds.client_id = "client123"
    mock_creds.client_secret = "secret456"
    mock_creds.scopes = ["scope1", "scope2"]

    result = credentials_to_dict(mock_creds)

    assert result == {
        "token": "test_token",
        "refresh_token": "test_refresh",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "client123",
        "client_secret": "secret456",
        "scopes": ["scope1", "scope2"],
    }


@pytest.mark.asyncio
async def test_give_session_creds_from_app_state() -> None:
    """Test give_session_creds retrieves from app.state."""
    from task_client_service.routers.auth_router import give_session_creds

    mock_request = MagicMock()
    creds_dict = {"token": "test_token"}
    mock_request.app.state.credentials = creds_dict

    response = await give_session_creds(mock_request)

    assert response.status_code == 200
    assert json.loads(bytes(response.body)) == creds_dict


@pytest.mark.asyncio
async def test_give_session_creds_from_session() -> None:
    """Test give_session_creds retrieves from session when not in app.state."""
    from task_client_service.routers.auth_router import give_session_creds

    mock_request = MagicMock()
    creds_dict = {"token": "test_token"}

    # No credentials in app.state
    mock_request.app.state = MagicMock(spec=[])

    # But credentials exist in session
    mock_request.session = {"credentials": json.dumps(creds_dict)}

    response = await give_session_creds(mock_request)

    assert response.status_code == 200
    assert json.loads(bytes(response.body)) == creds_dict


@pytest.mark.asyncio
async def test_give_session_creds_not_found() -> None:
    """Test give_session_creds when no credentials exist."""
    from task_client_service.routers.auth_router import give_session_creds

    mock_request = MagicMock()
    mock_request.app.state = MagicMock(spec=[])
    mock_request.session = {}

    with pytest.raises(HTTPException) as exc_info:
        await give_session_creds(mock_request)

    assert exc_info.value.status_code == 401
    assert "No active session" in exc_info.value.detail
