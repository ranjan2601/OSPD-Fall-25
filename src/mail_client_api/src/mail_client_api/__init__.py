"""Mail Client API - Core protocols and contracts.

This module defines the core protocols (interfaces) for the mail client system.
It provides abstract contracts that concrete implementations must follow to
enable email retrieval, message management, and client operations.

Usage:
    from mail_client_api import get_client, Client

    # Get a client instance from an implementation
    client = get_client()  # Returns concrete implementation

    # Use the client to fetch messages
    messages = client.get_messages()
    for message in messages:
        print(f"Subject: {message.subject}")
"""

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

import sys
from pathlib import Path

message_path = Path(__file__).parent.parent.parent.parent / "message/src"
sys.path.append(str(message_path))

from message import Message

@runtime_checkable
class Client(Protocol):
    """A protocol representing a mail client for email operations.

    This protocol defines the interface for mail client implementations
    that can retrieve, delete, and manage email messages from a mail server.
    """

    def get_message(self, message_id: str) -> Message:
        """Return a message by its ID.

        Args:
            message_id (str): The ID of the message to retrieve.

        Returns:
            Message: The message object corresponding to the given ID.

        """
        raise NotImplementedError

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by its ID.

        Args:
            message_id (str): The ID of the message to delete.

        Returns:
            bool: True if the message was successfully deleted, False otherwise.

        """
        raise NotImplementedError

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read by its ID.

        Args:
            message_id (str): The ID of the message to mark as read.

        Returns:
            bool: True if the message was successfully marked as read, False otherwise.

        """
        raise NotImplementedError

    def get_messages(self, max_results: int = 10) -> Iterator[Message]:
        """Return an iterator of all messages in the inbox.

        Args:
            max_results (int, optional): The maximum number of messages to return. Defaults to 10.

        Returns:
            Iterator[Message]: An iterator yielding Message objects from the inbox.

        """
        raise NotImplementedError


class MockMessage:
    """Mock message implementation for testing."""
    
    def __init__(self, id: str, subject: str, body: str, from_: str, to: str = "test@recipient.com", date: str = "2023-01-01"):
        self._id = id
        self._subject = subject
        self._body = body
        self._from = from_
        self._to = to
        self._date = date
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def from_(self) -> str:
        return self._from
    
    @property
    def to(self) -> str:
        return self._to
    
    @property
    def date(self) -> str:
        return self._date
    
    @property
    def subject(self) -> str:
        return self._subject
    
    @property
    def body(self) -> str:
        return self._body


class MockClient(Client):
    """Mock client implementation for testing."""
    
    def get_message(self, message_id: str) -> Message:
        return MockMessage(
            id="test_id",
            subject="API Working",
            body="The API is working correctly",
            from_="test@example.com"
        )

    def delete_message(self, message_id: str) -> bool:
        return True
    
    def mark_as_read(self, message_id: str) -> bool:
        return True

    def get_messages(self, max_results: int = 10) -> Iterator[Message]:
        messages = [
            MockMessage(
                id="test_id_1",
                subject="API Working",
                body="The API is working correctly",
                from_="test@example.com"
            ),
            MockMessage(
                id="test_id_2", 
                subject="Another Test Message",
                body="This is another test message",
                from_="test2@example.com"
            )
        ]
        return iter(messages)

def get_client(interactive: bool = False) -> Client:
    """Return a mock client for testing."""
    return MockClient()
