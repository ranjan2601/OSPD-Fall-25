"""Gmail Client Implementation Package.

This package provides a concrete implementation of the mail client API using the Gmail API.
It handles OAuth2 authentication and provides methods to interact with Gmail messages.

The main class `GmailClient` implements the `mail_client_api.Client` protocol and supports
multiple authentication modes for different environments.

Classes:
    GmailClient: Main client class implementing the mail_client_api.Client protocol.

Functions:
    get_client_impl: Factory function to create a GmailClient instance.

Example:
    ```python
    from gmail_client_impl import GmailClient
    client = GmailClient()
    messages = list(client.get_messages())
    ```

"""

import mail_client_api

from ._impl import GmailClient

# Export the main class so it's documented by mkdocstrings
__all__ = ["GmailClient", "get_client_impl"]


def get_client_impl(interactive: bool = False) -> mail_client_api.Client:
    """Get an instance of the GmailClient.

    This factory function creates and returns a new GmailClient instance
    with default authentication handling.

    Args:
        interactive (bool): If True, the client may prompt for user input
        during initialization (e.g., for OAuth2 flow). If False, it will
        use environment variables or other non-interactive methods.

    Returns:
        mail_client_api.Client: A GmailClient instance implementing the
        mail_client_api.Client protocol.

    """
    return GmailClient(interactive=interactive)


# --- Dependency Injection ---
# Override the get_client function in the protocol package
# Now, anyone calling mail_client_api.get_client() will get our implementation.
mail_client_api.get_client = get_client_impl
# --- Dependency Injection ---
