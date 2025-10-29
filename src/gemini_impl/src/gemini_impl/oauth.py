"""OAuth 2.0 authentication handler for Google Gemini API.

This module handles the OAuth 2.0 flow for authenticating users with Google
and managing credentials in memory for the current session.
"""

import json
from pathlib import Path
from typing import Any, ClassVar

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow


class OAuthManager:
    """Manages OAuth 2.0 authentication for the current session.

    Stores credentials in memory for the duration of the session.
    Credentials are not persisted to disk.

    Attributes:
        credentials_file: Path to Google OAuth credentials JSON file.
        scopes: List of OAuth scopes required by the application.

    """

    # Scopes for Gmail integration (Gemini API uses API key, not OAuth)
    # These scopes allow the app to read and modify user's Gmail
    SCOPES: ClassVar[list[str]] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    def __init__(
        self,
        credentials_file: str,
        db_path: str | None = None,
        scopes: list[str] | None = None,
    ) -> None:
        """Initialize the OAuth manager.

        Args:
            credentials_file: Path to the OAuth credentials JSON file
                             (downloaded from Google Cloud Console).
            db_path: Deprecated parameter, kept for backward compatibility.
            scopes: List of OAuth scopes. Defaults to SCOPES if not provided.

        Raises:
            FileNotFoundError: If credentials_file does not exist.
            ValueError: If credentials_file is empty.

        """
        if not credentials_file:
            msg = "credentials_file cannot be empty"
            raise ValueError(msg)

        cred_path = Path(credentials_file)
        if not cred_path.exists():
            msg = f"Credentials file not found: {credentials_file}"
            raise FileNotFoundError(msg)

        self.credentials_file = credentials_file
        self.db_path = db_path  # Kept for backward compatibility, not used
        self.scopes = scopes or self.SCOPES
        # In-memory storage for user credentials
        self._credentials_cache: dict[str, Any] = {}

    def get_authorization_url(self, user_id: str) -> str:
        """Generate the OAuth authorization URL for a user.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            The authorization URL to redirect the user to.

        Raises:
            ValueError: If user_id is empty.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)

        # Load client config from credentials file
        with Path(self.credentials_file).open() as f:
            client_config = json.load(f)

        # Create Flow for web app OAuth
        flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes,
            redirect_uri="http://localhost:8000/auth/callback",
        )

        # Generate authorization URL
        auth_url, _state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
        )
        return auth_url

    def handle_callback(self, user_id: str, code: str) -> Credentials:
        """Handle the OAuth callback and exchange code for credentials.

        Args:
            user_id: Unique identifier for the user.
            code: Authorization code from the callback.

        Returns:
            Google Credentials object.

        Raises:
            ValueError: If user_id or code is empty.
            Exception: If code exchange fails.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)
        if not code:
            msg = "code cannot be empty"
            raise ValueError(msg)

        # Load client config from credentials file
        with Path(self.credentials_file).open() as f:
            client_config = json.load(f)

        # Create Flow for web app OAuth
        flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes,
            redirect_uri="http://localhost:8000/auth/callback",
        )

        # Exchange code for credentials
        credentials = flow.fetch_token(code=code)

        # Store credentials in memory
        self._credentials_cache[user_id] = credentials

        return credentials

    def get_credentials(self, user_id: str) -> Credentials | None:
        """Retrieve credentials for a user if available.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            Google Credentials object, or None if not found.

        Raises:
            ValueError: If user_id is empty.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)

        credentials_data = self._credentials_cache.get(user_id)
        if not credentials_data:
            return None

        # Recreate Credentials object from cached data
        if isinstance(credentials_data, dict):
            credentials = Credentials(
                token=credentials_data.get("access_token"),
                refresh_token=credentials_data.get("refresh_token"),
                token_uri=credentials_data.get("token_uri"),
                client_id=credentials_data.get("client_id"),
                client_secret=credentials_data.get("client_secret"),
            )
        else:
            # Already a Credentials object
            credentials = credentials_data

        # Refresh token if expired
        if credentials and credentials.expired and credentials.refresh_token:
            request = Request()
            credentials.refresh(request)
            # Update cached credentials with new token
            self._credentials_cache[user_id] = credentials

        return credentials

    def revoke_credentials(self, user_id: str) -> bool:
        """Revoke and delete credentials for a user from memory.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            True if credentials were deleted, False otherwise.

        Raises:
            ValueError: If user_id is empty.

        """
        if not user_id:
            msg = "user_id cannot be empty"
            raise ValueError(msg)

        if user_id in self._credentials_cache:
            del self._credentials_cache[user_id]
            return True
        return False

