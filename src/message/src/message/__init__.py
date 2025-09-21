"""Message Protocol - Core message representation.

This module defines the Message protocol (interface) that represents
an email message with its essential properties like sender, recipient,
subject, content, and metadata.

Usage:
    from message import Message, get_message

    # Get a message instance from an implementation
    msg = get_message(msg_id="123", raw_data="...")

    # Access message properties
    print(f"From: {msg.from_}")
    print(f"Subject: {msg.subject}")
    print(f"Body: {msg.body}")
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Message(Protocol):
    """A protocol representing an email message.

    This protocol defines the interface for accessing email message
    properties such as sender, recipient, subject, and content.
    """

    @property
    def id(self) -> str:
        """Return the unique identifier of the message.

        Returns:
            str: The unique message identifier.

        """
        raise NotImplementedError

    @property
    def from_(self) -> str:
        """Return the sender's email address.

        Returns:
            str: The email address of the message sender.

        """
        raise NotImplementedError

    @property
    def to(self) -> str:
        """Return the recipient's email address.

        Returns:
            str: The email address of the message recipient.

        """
        raise NotImplementedError

    @property
    def date(self) -> str:
        """Return the date the message was sent.

        Returns:
            str: The date string when the message was sent.

        """
        raise NotImplementedError

    @property
    def subject(self) -> str:
        """Return the subject line of the message.

        Returns:
            str: The message subject line.

        """
        raise NotImplementedError

    @property
    def body(self) -> str:
        """Return the plain text content of the message.

        Returns:
            str: The plain text body content of the message.

        """
        raise NotImplementedError


def get_message(msg_id: str, raw_data: str) -> Message:
    """Return an instance of a Message.

    Args:
        msg_id (str): The unique identifier for the message.
        raw_data (str): The raw data used to construct the message.

    Returns:
        Message: An instance conforming to the Message protocol.

    Raises:
        NotImplementedError: If the function is not overridden by an implementation.

    """
    raise NotImplementedError
