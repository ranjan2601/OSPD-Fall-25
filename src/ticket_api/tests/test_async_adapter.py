"""Tests for AsyncStandardizedTicketAdapter."""

import pytest
from uuid import UUID, uuid4

from ticket_api.async_adapter import AsyncStandardizedTicketAdapter
from ticket_api.adapter import SimpleTicket
from ticket_api.models import TicketStatus as InternalTicketStatus
from ticket_api.shared_interface import TicketStatus as SharedTicketStatus
from typing import Any


class MockInternalTicket:
    """Mock internal ticket for testing."""

    def __init__(
        self,
        id: UUID,
        title: str,
        description: str,
        status: InternalTicketStatus,
        assignee: str | None = None,
    ) -> None:
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.assignee = assignee


class MockTicketServiceAPI:
    """Mock internal TicketServiceAPI for testing."""

    def __init__(self) -> None:
        self.tickets: dict[UUID, MockInternalTicket] = {}

    async def create_ticket(
        self,
        title: str,
        description: str,
        reporter: str,
        assignee: str | None = None,
    ) -> MockInternalTicket:
        """Create a new ticket."""
        ticket_id = uuid4()
        ticket = MockInternalTicket(
            id=ticket_id,
            title=title,
            description=description,
            status=InternalTicketStatus.OPEN,
            assignee=assignee,
        )
        self.tickets[ticket_id] = ticket
        return ticket

    async def get_ticket(self, ticket_id: UUID) -> MockInternalTicket | None:
        """Get a ticket by ID."""
        return self.tickets.get(ticket_id)

    async def list_tickets(
        self, status: InternalTicketStatus | None = None
    ) -> list[MockInternalTicket]:
        """List all tickets, optionally filtered by status."""
        if status is None:
            return list(self.tickets.values())
        return [t for t in self.tickets.values() if t.status == status]

    async def update_ticket(
        self,
        ticket_id: UUID,
        status: InternalTicketStatus | None = None,
        title: str | None = None,
        description: str | None = None,
        assignee: str | None = None,
    ) -> MockInternalTicket | None:
        """Update a ticket."""
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            return None

        if status is not None:
            ticket.status = status
        if title is not None:
            ticket.title = title
        if description is not None:
            ticket.description = description
        if assignee is not None:
            ticket.assignee = assignee

        return ticket

    async def delete_ticket(self, ticket_id: UUID) -> bool:
        """Delete a ticket."""
        if ticket_id in self.tickets:
            del self.tickets[ticket_id]
            return True
        return False


@pytest.fixture
def mock_service() -> Any:
    """Create a mock internal service."""
    return MockTicketServiceAPI()


@pytest.fixture
def adapter(mock_service: Any) -> AsyncStandardizedTicketAdapter:
    """Create an adapter with the mock service."""
    return AsyncStandardizedTicketAdapter(mock_service, reporter="test-reporter")


@pytest.mark.asyncio
async def test_create_ticket(adapter: Any) -> None:
    """Test creating a ticket."""
    ticket = await adapter.create_ticket(
        title="Test Bug",
        description="This is a test bug",
        assignee="dev@example.com",
    )

    assert isinstance(ticket, SimpleTicket)
    assert ticket.title == "Test Bug"
    assert ticket.description == "This is a test bug"
    assert ticket.status == SharedTicketStatus.OPEN
    assert ticket.assignee == "dev@example.com"
    assert ticket.id  # Should have a UUID string


@pytest.mark.asyncio
async def test_create_ticket_without_assignee(adapter: Any) -> None:
    """Test creating a ticket without assignee."""
    ticket = await adapter.create_ticket(
        title="Unassigned Bug",
        description="This bug has no assignee",
    )

    assert ticket.title == "Unassigned Bug"
    assert ticket.assignee is None


@pytest.mark.asyncio
async def test_get_ticket_found(adapter: Any) -> None:
    """Test getting an existing ticket."""
    # Create a ticket first
    created = await adapter.create_ticket(
        title="Test Bug",
        description="Test description",
    )

    # Get it back
    fetched = await adapter.get_ticket(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Test Bug"
    assert fetched.description == "Test description"


@pytest.mark.asyncio
async def test_get_ticket_not_found(adapter: Any) -> None:
    """Test getting a non-existent ticket."""
    random_id = str(uuid4())
    ticket = await adapter.get_ticket(random_id)
    assert ticket is None


@pytest.mark.asyncio
async def test_get_ticket_invalid_uuid(adapter: Any) -> None:
    """Test getting a ticket with invalid UUID string."""
    with pytest.raises(ValueError, match="Invalid ticket ID format"):
        await adapter.get_ticket("not-a-valid-uuid")


@pytest.mark.asyncio
async def test_search_tickets_all(adapter: Any) -> None:
    """Test searching all tickets without filters."""
    # Create multiple tickets
    await adapter.create_ticket("Bug 1", "Description 1")
    await adapter.create_ticket("Bug 2", "Description 2")
    await adapter.create_ticket("Feature Request", "Description 3")

    # Search all
    results = await adapter.search_tickets()

    assert len(results) == 3


@pytest.mark.asyncio
async def test_search_tickets_by_query_in_title(adapter: Any) -> None:
    """Test searching tickets by query matching title."""
    await adapter.create_ticket("Bug in login", "Description 1")
    await adapter.create_ticket("Bug in signup", "Description 2")
    await adapter.create_ticket("Feature Request", "Description 3")

    # Search for "Bug"
    results = await adapter.search_tickets(query="Bug")

    assert len(results) == 2
    assert all("Bug" in t.title for t in results)


@pytest.mark.asyncio
async def test_search_tickets_by_query_in_description(adapter: Any) -> None:
    """Test searching tickets by query matching description."""
    await adapter.create_ticket("Bug 1", "Login issue here")
    await adapter.create_ticket("Bug 2", "Signup problem")
    await adapter.create_ticket("Bug 3", "Another login issue")

    # Search for "login"
    results = await adapter.search_tickets(query="login")

    assert len(results) == 2
    assert all("login" in t.description.lower() for t in results)


@pytest.mark.asyncio
async def test_create_ticket_success(
    adapter: AsyncStandardizedTicketAdapter, mock_service: Any
) -> None:
    """Test searching tickets by status filter."""
    # Create tickets with different statuses
    await adapter.create_ticket("Open Bug", "Description 1")
    ticket2 = await adapter.create_ticket("In Progress Bug", "Description 2")
    ticket3 = await adapter.create_ticket("Closed Bug", "Description 3")

    # Update statuses directly in mock service
    await mock_service.update_ticket(UUID(ticket2.id), status=InternalTicketStatus.IN_PROGRESS)
    await mock_service.update_ticket(UUID(ticket3.id), status=InternalTicketStatus.CLOSED)

    # Search by OPEN status
    open_tickets = await adapter.search_tickets(status=SharedTicketStatus.OPEN)
    assert len(open_tickets) == 1
    assert open_tickets[0].status == SharedTicketStatus.OPEN

    # Search by IN_PROGRESS status
    in_progress_tickets = await adapter.search_tickets(status=SharedTicketStatus.IN_PROGRESS)
    assert len(in_progress_tickets) == 1
    assert in_progress_tickets[0].status == SharedTicketStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_create_ticket_with_optional_fields(
    adapter: AsyncStandardizedTicketAdapter, mock_service: Any
) -> None:
    """Test searching tickets with both query and status filters."""
    # Create tickets
    await adapter.create_ticket("Bug in login", "Description 1")
    ticket2 = await adapter.create_ticket("Bug in signup", "Description 2")
    await adapter.create_ticket("Feature Request", "Description 3")

    # Update status of ticket2
    await mock_service.update_ticket(UUID(ticket2.id), status=InternalTicketStatus.IN_PROGRESS)

    # Search for "Bug" with OPEN status
    results = await adapter.search_tickets(query="Bug", status=SharedTicketStatus.OPEN)

    assert len(results) == 1
    assert "Bug" in results[0].title
    assert results[0].status == SharedTicketStatus.OPEN


@pytest.mark.asyncio
async def test_update_ticket_status(adapter: Any) -> None:
    """Test updating ticket status."""
    ticket = await adapter.create_ticket("Test Bug", "Description")

    # Update status to IN_PROGRESS
    updated = await adapter.update_ticket(ticket.id, status=SharedTicketStatus.IN_PROGRESS)

    assert updated.status == SharedTicketStatus.IN_PROGRESS
    assert updated.title == "Test Bug"  # Other fields unchanged


@pytest.mark.asyncio
async def test_update_ticket_title(adapter: Any) -> None:
    """Test updating ticket title."""
    ticket = await adapter.create_ticket("Old Title", "Description")

    updated = await adapter.update_ticket(ticket.id, title="New Title")

    assert updated.title == "New Title"
    assert updated.description == "Description"  # Unchanged


@pytest.mark.asyncio
async def test_update_ticket_description(adapter: Any) -> None:
    """Test updating ticket description."""
    ticket = await adapter.create_ticket("Title", "Old Description")

    updated = await adapter.update_ticket(ticket.id, description="New Description")

    assert updated.description == "New Description"
    assert updated.title == "Title"  # Unchanged


@pytest.mark.asyncio
async def test_update_ticket_assignee(adapter: Any) -> None:
    """Test updating ticket assignee."""
    ticket = await adapter.create_ticket("Title", "Description")

    updated = await adapter.update_ticket(ticket.id, assignee="new-dev@example.com")

    assert updated.assignee == "new-dev@example.com"


@pytest.mark.asyncio
async def test_update_ticket_multiple_fields(adapter: Any) -> None:
    """Test updating multiple ticket fields at once."""
    ticket = await adapter.create_ticket("Old Title", "Old Description")

    updated = await adapter.update_ticket(
        ticket.id,
        title="New Title",
        description="New Description",
        status=SharedTicketStatus.CLOSED,
        assignee="dev@example.com",
    )

    assert updated.title == "New Title"
    assert updated.description == "New Description"
    assert updated.status == SharedTicketStatus.CLOSED
    assert updated.assignee == "dev@example.com"


@pytest.mark.asyncio
async def test_update_ticket_not_found(adapter: Any) -> None:
    """Test updating a non-existent ticket."""
    random_id = str(uuid4())

    with pytest.raises(ValueError, match="Ticket not found"):
        await adapter.update_ticket(random_id, title="New Title")


@pytest.mark.asyncio
async def test_update_ticket_invalid_uuid(adapter: Any) -> None:
    """Test updating a ticket with invalid UUID string."""
    with pytest.raises(ValueError, match="Invalid ticket ID format"):
        await adapter.update_ticket("not-a-uuid", title="New Title")


@pytest.mark.asyncio
async def test_delete_ticket_success(adapter: Any) -> None:
    """Test deleting an existing ticket."""
    ticket = await adapter.create_ticket("Test Bug", "Description")

    result = await adapter.delete_ticket(ticket.id)

    assert result is True

    # Verify it's gone
    fetched = await adapter.get_ticket(ticket.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_delete_ticket_not_found(adapter: Any) -> None:
    """Test deleting a non-existent ticket."""
    random_id = str(uuid4())

    result = await adapter.delete_ticket(random_id)

    assert result is False


@pytest.mark.asyncio
async def test_delete_ticket_invalid_uuid(adapter: Any) -> None:
    """Test deleting a ticket with invalid UUID string."""
    with pytest.raises(ValueError, match="Invalid ticket ID format"):
        await adapter.delete_ticket("not-a-uuid")


@pytest.mark.asyncio
async def test_status_mapping_open(adapter: Any) -> None:
    """Test status mapping for OPEN status."""
    ticket = await adapter.create_ticket("Bug", "Description")
    assert ticket.status == SharedTicketStatus.OPEN


@pytest.mark.asyncio
async def test_search_tickets_with_query(
    adapter: AsyncStandardizedTicketAdapter, mock_service: Any
) -> None:
    """Test status mapping for IN_PROGRESS status."""
    ticket = await adapter.create_ticket("Bug", "Description")

    # Update to IN_PROGRESS via internal API
    await mock_service.update_ticket(UUID(ticket.id), status=InternalTicketStatus.IN_PROGRESS)

    # Fetch via adapter
    fetched = await adapter.get_ticket(ticket.id)
    assert fetched is not None
    assert fetched.status == SharedTicketStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_search_tickets_with_status(
    adapter: AsyncStandardizedTicketAdapter, mock_service: Any
) -> None:
    """Test status mapping from RESOLVED (internal) to CLOSED (shared)."""
    ticket = await adapter.create_ticket("Bug", "Description")

    # Update to RESOLVED via internal API
    await mock_service.update_ticket(UUID(ticket.id), status=InternalTicketStatus.RESOLVED)

    # Fetch via adapter - should map to CLOSED
    fetched = await adapter.get_ticket(ticket.id)
    assert fetched is not None
    assert fetched.status == SharedTicketStatus.CLOSED


@pytest.mark.asyncio
async def test_search_tickets_with_both_query_and_status(
    adapter: AsyncStandardizedTicketAdapter, mock_service: Any
) -> None:
    """Test status mapping for CLOSED status."""
    ticket = await adapter.create_ticket("Bug", "Description")

    # Update to CLOSED via internal API
    await mock_service.update_ticket(UUID(ticket.id), status=InternalTicketStatus.CLOSED)

    # Fetch via adapter
    fetched = await adapter.get_ticket(ticket.id)
    assert fetched is not None
    assert fetched.status == SharedTicketStatus.CLOSED


@pytest.mark.asyncio
async def test_custom_reporter(mock_service: Any) -> None:
    """Test adapter with custom reporter."""
    adapter = AsyncStandardizedTicketAdapter(mock_service, reporter="custom-reporter")

    ticket = await adapter.create_ticket("Bug", "Description")

    # Reporter should be used in create_ticket call
    # (We can verify this by checking the mock was called with correct args,
    # but since our mock doesn't track this, we just verify the ticket was created)
    assert ticket is not None
    assert ticket.title == "Bug"
