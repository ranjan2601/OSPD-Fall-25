"""OAuth 2.0 authentication handler for Google Gemini API.

This module handles the OAuth 2.0 flow for authenticating users with Google,
storing credentials securely, and managing token refresh.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, ClassVar

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow


class OAuthManager:
    """Manages OAuth 2.0 authentication and credential storage.

    Attributes:
        credentials_file: Path to Google OAuth credentials JSON file.
        db_path: Path to SQLite database for storing user tokens.
        scopes: List of OAuth scopes required by the application.

    """

    # Scopes needed for Gemini API and Gmail integration
    SCOPES: ClassVar[list[str]] = [
        "https://www.googleapis.com/auth/generative-language",
    ]

    def __init__(
        self,
        credentials_file: str,
        db_path: str = "conversations.db",
        scopes: list[str] | None = None,
    ) -> None:
        """Initialize the OAuth manager.

        Args:
            credentials_file: Path to the OAuth credentials JSON file
                             (downloaded from Google Cloud Console).
            db_path: Path to SQLite database for storing tokens.
            scopes: List of OAuth scopes. Defaults to SCOPES if not provided.

        Raises:
            FileNotFoundError: If credentials_file does not exist.
            ValueError: If credentials_file or db_path is empty.

        """
        if not credentials_file:
            msg = "credentials_file cannot be empty"
            raise ValueError(msg)
        if not db_path:
            msg = "db_path cannot be empty"
            raise ValueError(msg)

        cred_path = Path(credentials_file)
        if not cred_path.exists():
            msg = f"Credentials file not found: {credentials_file}"
            raise FileNotFoundError(msg)

        self.credentials_file = credentials_file
        self.db_path = db_path
        self.scopes = scopes or self.SCOPES
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database for storing user tokens."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS oauth_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL UNIQUE,
                    token TEXT NOT NULL,
                    refresh_token TEXT,
                    token_uri TEXT,
                    client_id TEXT,
                    client_secret TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_id ON oauth_tokens(user_id)",
            )
            conn.commit()

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
        return auth_url  # type: ignore[no-any-return]

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

        # Store credentials
        self._store_credentials(user_id, credentials)

        return credentials  # type: ignore[no-any-return]

    def get_credentials(self, user_id: str) -> Credentials | None:
        """Retrieve and refresh credentials for a user if needed.

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

        credentials_data = self._get_stored_credentials(user_id)
        if not credentials_data:
            return None

        # Recreate Credentials object from stored data
        credentials = Credentials(  # type: ignore[no-untyped-call]
            token=credentials_data.get("token"),
            refresh_token=credentials_data.get("refresh_token"),
            token_uri=credentials_data.get("token_uri"),
            client_id=credentials_data.get("client_id"),
            client_secret=credentials_data.get("client_secret"),
        )

        # Refresh token if expired
        if credentials and credentials.expired and credentials.refresh_token:
            request = Request()  # type: ignore[no-untyped-call]
            credentials.refresh(request)
            # Update stored credentials with new token
            self._store_credentials(user_id, credentials)

        return credentials

    def revoke_credentials(self, user_id: str) -> bool:
        """Revoke and delete stored credentials for a user.

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

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM oauth_tokens WHERE user_id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _store_credentials(
        self,
        user_id: str,
        credentials: Any,  # noqa: ANN401
    ) -> None:
        """Store credentials in the database.

        Args:
            user_id: Unique identifier for the user.
            credentials: Credentials object or dict with credential data.

        """
        if isinstance(credentials, dict):
            token = credentials.get("access_token")
            refresh_token = credentials.get("refresh_token")
            token_uri = credentials.get("token_uri")
            client_id = credentials.get("client_id")
            client_secret = credentials.get("client_secret")
        else:
            token = credentials.token
            refresh_token = credentials.refresh_token
            token_uri = credentials.token_uri
            client_id = getattr(credentials, "client_id", None)
            client_secret = getattr(credentials, "client_secret", None)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO oauth_tokens
                (user_id, token, refresh_token, token_uri, client_id, client_secret)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                token = excluded.token,
                refresh_token = excluded.refresh_token,
                updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, token, refresh_token, token_uri, client_id, client_secret),
            )
            conn.commit()

    def _get_stored_credentials(self, user_id: str) -> dict[str, Any] | None:
        """Retrieve stored credentials from the database.

        Args:
            user_id: Unique identifier for the user.

        Returns:
            Dictionary with credential data, or None if not found.

        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT token, refresh_token, token_uri, client_id, client_secret
                FROM oauth_tokens WHERE user_id = ?
                """,
                (user_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return {
            "token": row[0],
            "refresh_token": row[1],
            "token_uri": row[2],
            "client_id": row[3],
            "client_secret": row[4],
        }
