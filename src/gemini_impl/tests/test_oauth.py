"""Tests for OAuth 2.0 authentication manager."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from gemini_impl.oauth import OAuthManager


@pytest.fixture
def mock_credentials_file() -> str:
    """Create a mock credentials file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
    ) as f:
        credentials = {
            "web": {
                "client_id": "test-client-id.apps.googleusercontent.com",
                "client_secret": "test-secret",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080/callback"],
            },
        }
        json.dump(credentials, f)
        return f.name


class TestOAuthManagerInit:
    """Test OAuthManager initialization."""

    def test_init_with_valid_credentials(self, mock_credentials_file: str) -> None:
        """Test initializing with valid credentials file."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )
        assert manager.credentials_file == mock_credentials_file

    def test_init_with_empty_credentials_file(self) -> None:
        """Test that empty credentials_file raises ValueError."""
        with pytest.raises(ValueError, match="credentials_file cannot be empty"):
            OAuthManager(credentials_file="")

    def test_init_with_missing_credentials_file(self) -> None:
        """Test that missing credentials file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            OAuthManager(
                credentials_file="/nonexistent/path/creds.json",
            )

    def test_init_with_optional_db_path(self, mock_credentials_file: str) -> None:
        """Test that db_path is now optional and kept for backward compatibility."""
        # db_path is now optional (deprecated parameter)
        manager = OAuthManager(credentials_file=mock_credentials_file)
        assert manager.credentials_file == mock_credentials_file
        assert manager.db_path is None

    def test_init_in_memory_storage(self, mock_credentials_file: str) -> None:
        """Test that OAuthManager uses in-memory storage for credentials."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
            db_path=None,
        )
        # Verify in-memory storage is initialized
        assert hasattr(manager, "_credentials_cache")
        assert isinstance(manager._credentials_cache, dict)
        assert len(manager._credentials_cache) == 0


class TestOAuthManagerGetAuthorizationUrl:
    """Test get_authorization_url method."""

    def test_get_authorization_url_with_valid_user(
        self,
        mock_credentials_file: str,
    ) -> None:
        """Test generating authorization URL."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        with patch(
            "gemini_impl.oauth.Flow.from_client_config",
        ) as mock_flow_class:
            mock_flow_instance = MagicMock()
            mock_flow_class.return_value = mock_flow_instance
            mock_flow_instance.authorization_url.return_value = (
                "https://accounts.google.com/o/oauth2/auth?...",
                "state-token",
            )

            url = manager.get_authorization_url("user123")
            assert url == "https://accounts.google.com/o/oauth2/auth?..."

    def test_get_authorization_url_empty_user_id(
        self,
        mock_credentials_file: str,
    ) -> None:
        """Test that empty user_id raises ValueError."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            manager.get_authorization_url("")


class TestOAuthManagerHandleCallback:
    """Test handle_callback method."""

    def test_handle_callback_success(self, mock_credentials_file: str) -> None:
        """Test handling OAuth callback successfully."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        with patch(
            "gemini_impl.oauth.Flow.from_client_config",
        ) as mock_flow_class:
            mock_flow_instance = MagicMock()
            mock_flow_class.return_value = mock_flow_instance
            mock_credentials = {
                "access_token": "test-token",
                "refresh_token": "test-refresh-token",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "test-client-id",
                "client_secret": "test-secret",
            }
            mock_flow_instance.fetch_token.return_value = mock_credentials

            result = manager.handle_callback("user123", "auth-code-123")
            assert result is not None
            mock_flow_instance.fetch_token.assert_called_once_with(
                code="auth-code-123",
            )

    def test_handle_callback_empty_user_id(self, mock_credentials_file: str) -> None:
        """Test that empty user_id raises ValueError."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            manager.handle_callback("", "code")

    def test_handle_callback_empty_code(self, mock_credentials_file: str) -> None:
        """Test that empty code raises ValueError."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        with pytest.raises(ValueError, match="code cannot be empty"):
            manager.handle_callback("user123", "")


class TestOAuthManagerGetCredentials:
    """Test get_credentials method."""

    def test_get_credentials_not_found(self, mock_credentials_file: str) -> None:
        """Test getting credentials for user with no stored credentials."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        result = manager.get_credentials("nonexistent-user")
        assert result is None

    def test_get_credentials_empty_user_id(self, mock_credentials_file: str) -> None:
        """Test that empty user_id raises ValueError."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            manager.get_credentials("")

    def test_get_credentials_after_storage(self, mock_credentials_file: str) -> None:
        """Test retrieving credentials after storing them in memory."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        # Store credentials in memory (simulating callback)
        mock_creds_dict = {
            "access_token": "test-token",
            "refresh_token": "test-refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test-id",
            "client_secret": "test-secret",
        }
        manager._credentials_cache["user123"] = mock_creds_dict

        # Retrieve credentials
        result = manager.get_credentials("user123")
        assert result is not None
        assert result.token == "test-token"
        assert result.refresh_token == "test-refresh"


class TestOAuthManagerRevokeCredentials:
    """Test revoke_credentials method."""

    def test_revoke_credentials_success(self, mock_credentials_file: str) -> None:
        """Test revoking credentials successfully from memory."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        # Store credentials first in memory
        mock_creds_dict = {
            "access_token": "test-token",
            "refresh_token": "test-refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test-id",
            "client_secret": "test-secret",
        }
        manager._credentials_cache["user123"] = mock_creds_dict

        # Verify stored
        assert manager.get_credentials("user123") is not None

        # Revoke
        result = manager.revoke_credentials("user123")
        assert result is True

        # Verify deleted
        assert manager.get_credentials("user123") is None

    def test_revoke_credentials_nonexistent_user(
        self,
        mock_credentials_file: str,
    ) -> None:
        """Test revoking credentials for user with no stored credentials."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        result = manager.revoke_credentials("nonexistent-user")
        assert result is False

    def test_revoke_credentials_empty_user_id(
        self,
        mock_credentials_file: str,
    ) -> None:
        """Test that empty user_id raises ValueError."""
        manager = OAuthManager(
            credentials_file=mock_credentials_file,
        )

        with pytest.raises(ValueError, match="user_id cannot be empty"):
            manager.revoke_credentials("")
