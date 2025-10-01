from collections.abc import Iterator

import mail_client_api
from mail_client_api import message

from .generated.mail_client_service_api_client.api.default import (
    delete_message_messages_message_id_delete,
    get_message_messages_message_id_get,
    get_messages_messages_get,
    mark_as_read_messages_message_id_read_put,
)
from .generated.mail_client_service_api_client.client import Client as GeneratedClient
from .generated.mail_client_service_api_client.models.message_response import MessageResponse


class ServiceMessage(message.Message):
    """Message implementation for service responses."""

    def __init__(self, response: MessageResponse) -> None:
        """Initialize message from service response.

        Args:
            response: MessageResponse from the auto-generated client.

        """
        self._response = response

    @property
    def id(self) -> str:
        """Return the unique identifier of the message."""
        return self._response.id

    @property
    def from_(self) -> str:
        """Return the sender's email address."""
        return self._response.from_

    @property
    def to(self) -> str:
        """Return the recipient's email address."""
        return self._response.to

    @property
    def date(self) -> str:
        """Return the date the message was sent."""
        return self._response.date

    @property
    def subject(self) -> str:
        """Return the subject line of the message."""
        return self._response.subject

    @property
    def body(self) -> str:
        """Return the plain text content of the message."""
        return self._response.body


class ServiceClient(mail_client_api.Client):
    """HTTP client implementing the mail_client_api.Client protocol.

    This client communicates with a FastAPI mail service to provide the same
    interface as the direct Gmail client implementation.
    """

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """Initialize the service client.

        Args:
            base_url: Base URL of the mail service API.

        """
        self._client = GeneratedClient(base_url=base_url)

    def get_message(self, message_id: str) -> message.Message:
        """Return a message by its ID.

        Args:
            message_id: The ID of the message to retrieve.

        Returns:
            Message: The message object corresponding to the given ID.

        Raises:
            Exception: If the message cannot be retrieved.

        """
        response = get_message_messages_message_id_get.sync(
            client=self._client,
            message_id=message_id,
        )

        if response is None:
            msg = f"Message {message_id} not found"
            raise ValueError(msg)

        return ServiceMessage(response)

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by its ID.

        Args:
            message_id: The ID of the message to delete.

        Returns:
            bool: True if the message was successfully deleted, False otherwise.

        """
        response = delete_message_messages_message_id_delete.sync(
            client=self._client,
            message_id=message_id,
        )

        return response is not None and response.success

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read by its ID.

        Args:
            message_id: The ID of the message to mark as read.

        Returns:
            bool: True if the message was successfully marked as read, False otherwise.

        """
        response = mark_as_read_messages_message_id_read_put.sync(
            client=self._client,
            message_id=message_id,
        )

        return response is not None and response.success

    def get_messages(self, max_results: int = 10) -> Iterator[message.Message]:
        """Retrieve multiple messages from the inbox as an iterator.

        Args:
            max_results: Maximum number of messages to return.

        Returns:
            Iterator[Message]: Iterator yielding Message objects.

        """
        response = get_messages_messages_get.sync(
            client=self._client,
            max_results=max_results,
        )

        if response is None:
            return iter([])

        return iter(ServiceMessage(msg_response) for msg_response in response)
