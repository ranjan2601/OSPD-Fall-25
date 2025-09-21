"""Gmail Message Implementation - Concrete implementation of the Message protocol.

This package provides a concrete implementation of the Message protocol specifically
for Gmail messages. It includes the GmailMessage class that can parse and decode
Gmail API message data.

Usage:
    from gmail_message_impl import get_message_impl

    # Create a message instance from Gmail data
    message = get_message_impl(msg_id="12345", raw_data="base64_encoded_data")

    # Access message properties
    print(f"From: {message.from_}")
    print(f"Subject: {message.subject}")

The package automatically registers itself as the implementation for the
message.get_message() factory function through dependency injection.
"""

import message

from ._impl import GmailMessage


def get_message_impl(msg_id: str, raw_data: str) -> message.Message:
    """Return an instance of the concrete GmailMessage implementation.

    This factory function creates a GmailMessage instance that implements
    the Message protocol. It serves as the concrete implementation for
    the message.get_message() factory function.

    Args:
        msg_id (str): The unique identifier for the message from Gmail.
        raw_data (str): The base64url-encoded raw email data from Gmail API.

    Returns:
        message.Message: An instance of GmailMessage conforming to the Message protocol.

    Example:
        >>> msg = get_message_impl("12345", "encoded_data...")
        >>> print(msg.subject)
        "Important Email Subject"

    """
    return GmailMessage(msg_id=msg_id, raw_data=raw_data)


# --- Dependency Injection ---
# Override the get_message function in the protocol package
# Now, anyone calling message.get_message(id, data) will get our implementation.
message.get_message = get_message_impl
# --- Dependency Injection ---
