"""Gmail Client Implementation.

This module provides a concrete implementation of the mail client API using the Gmail API.
It handles OAuth2 authentication and provides methods to interact with Gmail messages.

The implementation supports multiple authentication modes:
    - Environment variables (for CI/CD environments)
    - Local token file (for development)
    - Interactive OAuth flow (for initial setup)

Classes:
    GmailClient: Main client class implementing the mail_client_api.Client protocol.

Example:
    Basic usage:

    ```python
    from gmail_client_impl import GmailClient
    client = GmailClient()
    messages = client.get_messages()
    ```

    With custom service:

    ```python
    from googleapiclient.discovery import build
    service = build('gmail', 'v1', credentials=creds)
    client = GmailClient(service=service)
    ```

    Force interactive authentication:

    ```python
    client = GmailClient(interactive=True)
    ```

"""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar

# --- CORE IMPORTS ---
# 1. Import the interfaces you are implementing and using.
import mail_client_api
import message  # <-- Import the message protocol package

# 2. Import the Google libraries needed for the implementation.
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]
from googleapiclient.discovery import Resource, build

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # If python-dotenv is not available, check if .env file exists
    # and manually load it
    env_path = Path(".env")
    if env_path.exists():
        with env_path.open() as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


class GmailClient(mail_client_api.Client):
    """Concrete implementation of the Client protocol using Gmail API.

    This class provides a complete implementation of the mail_client_api.Client protocol
    using Google's Gmail API. It handles OAuth2 authentication automatically and provides
    methods to interact with Gmail messages.

    Attributes:
        SCOPES: List of OAuth2 scopes required for Gmail API access.
        FAILURE_TO_CRED: Error message for authentication failures.
        service: The authenticated Gmail API service object.

    Authentication Flow:
        1. If `interactive=True`, forces interactive OAuth flow
        2. Try environment variables (GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN)
        3. Try local token.json file
        4. Fallback to interactive OAuth flow

    Environment Variables:
        - GMAIL_CLIENT_ID: OAuth2 client ID
        - GMAIL_CLIENT_SECRET: OAuth2 client secret
        - GMAIL_REFRESH_TOKEN: OAuth2 refresh token
        - GMAIL_TOKEN_URI: OAuth2 token URI (optional, defaults to Google's endpoint)

    Example:
        Basic usage:

        ```python
        client = GmailClient()
        messages = list(client.get_messages())
        ```

        Force interactive login:

        ```python
        client = GmailClient(interactive=True)
        ```

        With pre-configured service:

        ```python
        service = build('gmail', 'v1', credentials=my_creds)
        client = GmailClient(service=service)
        ```

    """

    SCOPES: ClassVar[list[str]] = [
        "https://www.googleapis.com/auth/gmail.modify",
    ]
    """OAuth2 scopes required for Gmail API access.
    
    The 'gmail.modify' scope allows reading, composing, and sending messages,
    as well as modifying labels and message metadata.
    """

    FAILURE_TO_CRED = "Failed to obtain credentials. Please check your setup."
    """Error message displayed when authentication fails."""

    def __init__(self, service: Resource | None = None, interactive: bool = False) -> None:
        """Initialize the GmailClient, handling authentication.

        This method handles the complete authentication flow for accessing the Gmail API.
        It supports multiple authentication methods and will automatically choose the
        best available option based on the environment and parameters.

        Args:
            service: An optional pre-configured Google API service resource.
                If provided, authentication is skipped and this service is used directly.
            interactive: If True, force interactive login, ignoring environment
                variables and existing token files. Useful for initial setup or
                when credentials need to be refreshed manually.

        Raises:
            RuntimeError: If authentication fails after trying all available methods.
            FileNotFoundError: If interactive mode is requested but credentials.json is missing.

        Note:
            The method will save credentials to 'token.json' for future use when
            authentication is successful through interactive flow or token refresh.

        """
        if service:
            self.service = service
            return  # Skip auth if service is provided

        creds: Credentials | None = None
        token_path = "token.json"
        creds_path = "credentials.json"

        # 1. Force Interactive Flow if requested
        if interactive:
            print("Interactive login requested, skipping environment variables and token file.")
            creds = self._run_interactive_flow(creds_path)

        # 2. Try Environment Variables (CI Mode) if not interactive
        if not creds and not interactive:
            client_id = os.environ.get("GMAIL_CLIENT_ID")
            client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
            refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")
            token_uri = os.environ.get("GMAIL_TOKEN_URI", "https://oauth2.googleapis.com/token")

            if client_id and client_secret and refresh_token:
                print("Attempting to authenticate using environment variables (CI mode)...")
                try:
                    creds = Credentials(  # type: ignore[no-untyped-call]
                        None,
                        refresh_token=refresh_token,
                        token_uri=token_uri,
                        client_id=client_id,
                        client_secret=client_secret,
                        scopes=self.SCOPES,
                    )
                    creds.refresh(Request())  # type: ignore[no-untyped-call]
                    print("Authentication via environment variables successful.")
                except Exception as e:
                    print(f"Error refreshing token from environment variables: {e}")
                    creds = None  # Ensure creds is None if refresh fails
                    # Don't raise here, allow fallback to file/interactive

        # 3. Try Token File if not interactive and env vars failed
        if not creds and not interactive:
            print("Attempting to authenticate using local token file...")
            if Path(token_path).exists():
                try:
                    creds = Credentials.from_authorized_user_file(  # type: ignore[no-untyped-call]
                        token_path,
                        self.SCOPES,
                    )
                    # Check if token needs refresh
                    if creds and not creds.valid and creds.refresh_token:
                        print("Refreshing token from file...")
                        try:
                            creds.refresh(Request())  # type: ignore[no-untyped-call]
                        except Exception as e:
                            print(f"Error refreshing token from file: {e}")
                            creds = None  # Force re-auth if refresh fails
                except Exception as e:
                    print(f"Error loading token from {token_path}: {e}")
                    creds = None  # Ensure creds is None if loading fails

        # 4. Fallback to Interactive Flow if all else fails (and not already done)
        if not creds or (creds and not creds.valid and not creds.refresh_token):
            if not interactive:  # Non-interactive mode should never fall back to interactive
                msg = (
                    "No valid credentials found and interactive mode is disabled. "
                    "Please provide valid credentials via environment variables or token file."
                )
                raise RuntimeError(msg)
            # Interactive mode was requested but failed
            print("No valid credentials found, running interactive login.")
            creds = self._run_interactive_flow(creds_path)
            if not creds:
                raise RuntimeError("Interactive authentication failed.")  # noqa: EM101 TRY003

        # --- End Authentication Logic --- #

        if not creds or not creds.valid:
            raise RuntimeError(self.FAILURE_TO_CRED)

        # Save the token if it was obtained interactively or refreshed
        if interactive or (creds.refresh_token and not Path(token_path).exists()):
            self._save_token(creds, token_path)

        # Build the service object
        try:
            self.service = build("gmail", "v1", credentials=creds)
            print("Gmail service built successfully.")
        except Exception as e:
            print(f"Error building Gmail service: {e}")
            raise  # Re-raise the exception

    def _run_interactive_flow(self, creds_path: str) -> Credentials | None:
        """Run the interactive OAuth flow.

        This method launches a local web server to handle the OAuth2 flow,
        opening the user's browser to complete authentication with Google.

        Args:
            creds_path: Path to the credentials.json file containing OAuth2 client configuration.

        Returns:
            Credentials object if authentication is successful, None if it fails.

        Raises:
            FileNotFoundError: If the credentials file doesn't exist.

        """
        print("Running interactive authentication flow...")
        if not Path(creds_path).exists():
            raise FileNotFoundError(f"'{creds_path}' not found. Cannot run interactive auth.")  # noqa: EM102 TRY003
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path,
                self.SCOPES,
            )
            return flow.run_local_server(port=0)  # type: ignore[no-any-return]
        except Exception as e:
            print(f"Error during interactive auth flow: {e}")
            raise

    def _save_token(self, creds: Credentials, token_path: str) -> None:
        """Save the credentials token to a file.

        Persists the OAuth2 credentials to a JSON file for future use,
        avoiding the need to re-authenticate on subsequent runs.

        Args:
            creds: The credentials object to save.
            token_path: Path where the token file should be saved.

        Note:
            The token file contains sensitive information and should be kept secure.
            It's automatically added to .gitignore in most project templates.

        """
        try:
            with Path(token_path).open("w") as token:
                token.write(creds.to_json())  # type: ignore[no-untyped-call]
            print(f"Credentials saved to {token_path}")
        except Exception as e:
            print(f"Error saving token to {token_path}: {e}")
            raise

    def get_message(self, message_id: str) -> message.Message:
        """Retrieve a specific message by its ID.

        Args:
            message_id: The unique identifier of the message to retrieve.

        Returns:
            A Message object containing the email data.

        Raises:
            Exception: If the message cannot be retrieved from the Gmail API.

        """
        try:
            msg_data = (
                self.service.users()  # type: ignore[attr-defined]
                .messages()
                .get(userId="me", id=message_id, format="raw")
                .execute()
            )
            raw_content = msg_data.get("raw")
            if not raw_content:
                msg = f"No raw content found for message {message_id}"
                raise ValueError(msg)

            # Use the factory from the abstract `message` package.
            # Do NOT call `GmailMessage()` directly.
            # Dependency injection ensures this call is routed to `gmail_message_impl` at runtime.
            return message.get_message(
                msg_id=message_id,
                raw_data=raw_content,
            )
        except Exception as e:
            print(f"Error retrieving message {message_id}: {e}")
            raise

    def delete_message(self, message_id: str) -> bool:
        """Delete a message from the mailbox.

        Args:
            message_id: The unique identifier of the message to delete.

        Returns:
            True if the message was successfully deleted, False otherwise.

        Note:
            This method permanently deletes the message from Gmail.
            The message cannot be recovered after deletion.

        """
        try:
            (
                self.service.users()  # type: ignore[attr-defined]
                .messages()
                .delete(userId="me", id=message_id)
                .execute()
            )
            print(f"Message {message_id} deleted successfully.")
            return True
        except Exception as e:
            print(f"Error deleting message {message_id}: {e}")
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read.

        Args:
            message_id: The unique identifier of the message to mark as read.

        Returns:
            True if the message was successfully marked as read, False otherwise.

        Note:
            This method removes the 'UNREAD' label from the message in Gmail,
            effectively marking it as read.

        """
        try:
            (
                self.service.users()  # type: ignore[attr-defined]
                .messages()
                .modify(
                    userId="me",
                    id=message_id,
                    body={"removeLabelIds": ["UNREAD"]},
                )
                .execute()
            )
            print(f"Message {message_id} marked as read successfully.")
            return True
        except Exception as e:
            print(f"Error marking message {message_id} as read: {e}")
            return False

    def get_messages(self, max_results: int = 10) -> Iterator[message.Message]:
        """Retrieve messages from the Gmail inbox.

        This method fetches a list of message summaries from the Gmail API,
        then retrieves the raw content for each message. It uses the
        `message.get_message` factory function to construct and yield
        a clean, protocol-compliant Message object for each email.

        Args:
            max_results: The maximum number of messages to retrieve.

        Yields:
            An iterator of `message.Message` objects.

        """
        results = (
            self.service.users()  # type: ignore[attr-defined]
            .messages()
            .list(userId="me", maxResults=max_results)
            .execute()
        )
        messages_summary = results.get("messages", [])

        for msg_summary in messages_summary:
            if "id" not in msg_summary:
                continue

            msg_data = (
                self.service.users()  # type: ignore[attr-defined]
                .messages()
                .get(userId="me", id=msg_summary["id"], format="raw")
                .execute()
            )
            raw_content = msg_data.get("raw")
            if raw_content:
                # Use the factory from the abstract `message` package.
                # Do NOT call `GmailMessage()` directly.
                # Dependency injection ensures this call is routed to `gmail_message_impl` at runtime.
                yield message.get_message(
                    msg_id=msg_summary["id"],
                    raw_data=raw_content,
                )
