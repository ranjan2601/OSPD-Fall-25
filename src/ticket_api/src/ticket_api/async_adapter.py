"""Async adapter to expose standardized TicketInterface from internal TicketServiceAPI.

This module provides an async compatibility layer for use in async contexts
like FastAPI endpoints, avoiding nested event loop errors from asyncio.run().
"""

import re
from typing import Any
from uuid import UUID

from tickets_api import Ticket
from tickets_api import TicketStatus as SharedTicketStatus

from .adapter import SimpleTicket
from .interface import TicketServiceAPI
from .models import TicketPriority as InternalTicketPriority
from .models import TicketStatus as InternalTicketStatus


class AsyncStandardizedTicketAdapter:
    """Async adapter that exposes async versions of TicketInterface methods.

    This adapter wraps an internal TicketServiceAPI implementation and provides
    async methods for use in async contexts (like FastAPI). It handles:
    - Async/await pattern (no nested event loops)
    - Mapping UUIDs to/from strings
    - Translating between internal and shared status enums
    - Simplifying ticket representations
    - Providing default values for internal-only fields

    Usage:
        internal_service = TicketImpl(user_id="user123", project_key="PROJ")
        adapter = AsyncStandardizedTicketAdapter(internal_service)

        # Use in async context
        ticket = await adapter.create_ticket(
            title="Bug in login",
            description="Users cannot log in",
            assignee="dev@example.com"
        )
    """

    def __init__(self, internal: TicketServiceAPI, reporter: str = "system") -> None:
        """Initialize the adapter with an internal TicketServiceAPI implementation.

        Args:
            internal: The internal TicketServiceAPI implementation to wrap
            reporter: Default reporter to use for ticket creation (since the
                     shared interface doesn't include reporter, but our internal
                     API requires it). Defaults to "system".

        """
        self._internal = internal
        self._reporter = reporter

    def _to_simple(self, internal_ticket: Any) -> SimpleTicket:
        """Convert an internal Ticket to a SimpleTicket.

        Args:
            internal_ticket: The internal feature-rich ticket

        Returns:
            A SimpleTicket exposing only the standardized fields

        """
        status_map = {
            InternalTicketStatus.OPEN: SharedTicketStatus.OPEN,
            InternalTicketStatus.IN_PROGRESS: SharedTicketStatus.IN_PROGRESS,
            InternalTicketStatus.RESOLVED: SharedTicketStatus.CLOSED,
            InternalTicketStatus.CLOSED: SharedTicketStatus.CLOSED,
        }

        # Add priority prefix to description so orchestrator can extract and display it
        description = internal_ticket.description
        if internal_ticket.priority:
            priority_value = internal_ticket.priority.value.upper()
            description = f"[PRIORITY: {priority_value}] {description}"

        return SimpleTicket(
            _id=str(internal_ticket.id),
            _title=internal_ticket.title,
            _description=description,
            _status=status_map[internal_ticket.status],
            _assignee=internal_ticket.assignee,
        )

    def _to_internal_status(
        self,
        shared_status: SharedTicketStatus,
    ) -> InternalTicketStatus:
        """Convert a shared status to internal status.

        Args:
            shared_status: Status from the standardized interface

        Returns:
            Corresponding internal status enum value

        """
        status_map = {
            SharedTicketStatus.OPEN: InternalTicketStatus.OPEN,
            SharedTicketStatus.IN_PROGRESS: InternalTicketStatus.IN_PROGRESS,
            SharedTicketStatus.CLOSED: InternalTicketStatus.CLOSED,
        }
        return status_map[shared_status]

    async def create_ticket(
        self,
        title: str,
        description: str,
        assignee: str | None = None,
    ) -> Ticket:
        """Create a new ticket.

        Args:
            title: Brief title describing the ticket
            description: Detailed description of the ticket
            assignee: Optional user ID to assign the ticket to

        Returns:
            The newly created Ticket instance

        Raises:
            ValueError: If title or description are invalid
            Exception: If ticket creation fails

        """
        # Parse priority from description if present
        priority = InternalTicketPriority.MEDIUM
        clean_description = description

        match = re.match(r"^\[PRIORITY: (LOW|MEDIUM|HIGH|CRITICAL)\]\s*", description)
        if match:
            priority_str = match.group(1).lower()
            try:
                priority = InternalTicketPriority(priority_str)
                clean_description = description[match.end() :]
            except ValueError:
                pass

        internal_ticket = await self._internal.create_ticket(
            title=title,
            description=clean_description,
            reporter=self._reporter,
            priority=priority,
            assignee=assignee,
        )
        return self._to_simple(internal_ticket)

    async def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Retrieve a ticket by its ID.

        Args:
            ticket_id: Unique identifier of the ticket to retrieve

        Returns:
            The Ticket instance if found, None otherwise

        Raises:
            ValueError: If ticket_id is not a valid UUID string
            Exception: If retrieval operation fails

        """
        try:
            uuid = UUID(ticket_id)
        except ValueError as e:
            msg = f"Invalid ticket ID format: {ticket_id}"
            raise ValueError(msg) from e

        internal_ticket = await self._internal.get_ticket(uuid)
        if internal_ticket is None:
            return None
        return self._to_simple(internal_ticket)

    async def search_tickets(
        self,
        query: str | None = None,
        status: SharedTicketStatus | None = None,
    ) -> list[Ticket]:
        """Search for tickets based on query and/or status.

        Args:
            query: Optional text query to search in title/description
            status: Optional status filter

        Returns:
            List of Ticket instances matching the criteria

        Raises:
            Exception: If search operation fails

        Note:
            The query parameter is implemented using client-side filtering
            since our internal API doesn't have a direct text search parameter.
            For production use, this could be optimized with a dedicated
            search endpoint.

        """
        internal_status = None
        if status is not None:
            internal_status = self._to_internal_status(status)

        internal_tickets = await self._internal.list_tickets(status=internal_status)

        if query:
            query_lower = query.lower()
            internal_tickets = [
                t
                for t in internal_tickets
                if query_lower in t.title.lower() or query_lower in t.description.lower()
            ]

        return [self._to_simple(t) for t in internal_tickets]

    async def update_ticket(
        self,
        ticket_id: str,
        status: SharedTicketStatus | None = None,
        title: str | None = None,
        description: str | None = None,
        assignee: str | None = None,
    ) -> Ticket:
        """Update a ticket's details.

        Args:
            ticket_id: Unique identifier of the ticket to update
            status: New status (optional)
            title: New title (optional)
            description: New description (optional)
            assignee: New assignee (optional)

        Returns:
            The updated Ticket instance

        Raises:
            ValueError: If ticket_id is invalid or ticket not found
            Exception: If update operation fails

        """
        try:
            uuid = UUID(ticket_id)
        except ValueError as e:
            msg = f"Invalid ticket ID format: {ticket_id}"
            raise ValueError(msg) from e

        internal_status = None
        if status is not None:
            internal_status = self._to_internal_status(status)

        internal_ticket = await self._internal.update_ticket(
            ticket_id=uuid,
            status=internal_status,
            title=title,
            description=description,
            assignee=assignee,
        )

        if internal_ticket is None:
            msg = f"Ticket not found: {ticket_id}"
            raise ValueError(msg)

        return self._to_simple(internal_ticket)

    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket. Returns True if successful.

        Args:
            ticket_id: Unique identifier of the ticket to delete

        Returns:
            True if the ticket was deleted, False if it wasn't found

        Raises:
            ValueError: If ticket_id is not a valid UUID string
            Exception: If deletion operation fails

        """
        try:
            uuid = UUID(ticket_id)
        except ValueError as e:
            msg = f"Invalid ticket ID format: {ticket_id}"
            raise ValueError(msg) from e

        return await self._internal.delete_ticket(uuid)
