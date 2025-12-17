"""FastAPI routes for AI-Chat Orchestrator service."""

import logging
import os
from typing import Any

import chat_client_api  # type: ignore[import]
from ai_chat_orchestrator.orchestrator import AIChatOrchestrator
from ai_chat_orchestrator.slack_chat_client import SlackChatClient
from ai_client_api.credential import resolve_api_key
from fastapi import APIRouter, HTTPException
from gemini_client_impl.client import GeminiClient
from pydantic import BaseModel, Field
from tickets_client_impl import TicketsClient

import discord_client_impl  # noqa: F401
import gemini_client_impl
from ticket_api import StandardizedTicketAdapter
from ticket_impl import TicketImpl
from tickets_api import TicketInterface, TicketStatus

gemini_client_impl.register()

logger = logging.getLogger(__name__)

router = APIRouter()

# Global orchestrator instances for different providers
_discord_orchestrator: Any = None
_slack_orchestrator: Any = None
_jira_ticket_client: TicketInterface | None = None
_gtasks_ticket_client: TicketInterface | None = None


def get_discord_orchestrator() -> Any:
    """Get or create the Discord orchestrator instance with Jira integration."""
    global _discord_orchestrator
    if _discord_orchestrator is None:
        try:
            gemini_api_key = resolve_api_key(user_id="service", provider="gemini")
            discord_user_id = os.getenv("DISCORD_USER_ID")

            # Create Discord orchestrator with Jira ticket client

            gemini_client_impl.register()
            discord_client_impl.register()

            ai_client = GeminiClient(api_key=gemini_api_key)

            chat_client = chat_client_api.get_client(user_id=discord_user_id)  # type: ignore[attr-defined]

            # Get Jira ticket client if configured
            ticket_client = None
            try:
                ticket_client = get_jira_ticket_client()
                logger.info("Jira ticket integration enabled for Discord")
            except Exception as e:
                logger.warning(f"Jira ticket integration not available: {e}")

            _discord_orchestrator = AIChatOrchestrator(
                ai_client=ai_client,
                chat_client=chat_client,
                system_prompt="You are a helpful AI assistant in a Discord channel.",
                ticket_client=ticket_client,
            )
            logger.info("Discord orchestrator initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize Discord orchestrator: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
    return _discord_orchestrator


def get_slack_orchestrator() -> Any:
    """Get or create the Slack orchestrator instance with Jira integration."""
    global _slack_orchestrator
    if _slack_orchestrator is None:
        try:
            gemini_api_key = resolve_api_key(user_id="service", provider="gemini")
            slack_token = os.getenv("SLACK_BOT_TOKEN", "")
            slack_base_url = os.getenv("SLACK_BASE_URL", "https://slack.com/api")

            # Create Slack orchestrator with Jira ticket client

            gemini_client_impl.register()
            ai_client = GeminiClient(api_key=gemini_api_key)
            chat_client = SlackChatClient(base_url=slack_base_url, token=slack_token)

            # Get Jira ticket client if configured
            ticket_client = None
            try:
                ticket_client = get_jira_ticket_client()
                logger.info("Jira ticket integration enabled for Slack")
            except Exception as e:
                logger.warning(f"Jira ticket integration not available: {e}")

            _slack_orchestrator = AIChatOrchestrator(
                ai_client=ai_client,
                chat_client=chat_client,
                system_prompt="You are a helpful AI assistant in a Slack channel.",
                ticket_client=ticket_client,
            )
            logger.info("Slack orchestrator initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize Slack orchestrator: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
    return _slack_orchestrator


def get_jira_ticket_client() -> TicketInterface:
    """Get or create the Jira ticket client instance."""
    global _jira_ticket_client
    if _jira_ticket_client is None:
        try:
            # Initialize Jira client with default user and project
            # TODO: Get these from environment variables or configuration
            user_id = os.getenv("JIRA_USER_ID", "default_user")
            project_key = os.getenv("JIRA_PROJECT_KEY", "PROJ")
            jira_impl = TicketImpl(user_id=user_id, project_key=project_key)
            # Wrap with adapter to expose TicketInterface
            _jira_ticket_client = StandardizedTicketAdapter(jira_impl)  # type: ignore[assignment]
            logger.info("Jira ticket client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Jira ticket client: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
    assert _jira_ticket_client is not None  # Guaranteed by initialization above
    return _jira_ticket_client


def get_gtasks_ticket_client() -> TicketInterface:
    """Get or create the Google Tasks ticket client instance."""
    global _gtasks_ticket_client
    if _gtasks_ticket_client is None:
        try:
            # Initialize Google Tasks client
            _gtasks_ticket_client = TicketsClient()
            logger.info("Google Tasks ticket client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Tasks ticket client: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
    return _gtasks_ticket_client


# Pydantic models
class ProcessMessageRequest(BaseModel):
    """Request model for processing a message."""

    channel_id: str = Field(..., description="The channel ID")
    user_input: str = Field(..., description="The user's message text")


class ProcessMessageResponse(BaseModel):
    """Response model from processing a message."""

    response: str = Field(..., description="The AI's response")
    success: bool = Field(..., description="Whether the operation succeeded")


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""

    content: str = Field(..., description="Message content to send")


class SendMessageResponse(BaseModel):
    """Response model for sending a message."""

    success: bool = Field(..., description="Whether the message was sent successfully")
    message_id: str | None = Field(None, description="ID of the sent message if available")


class ChannelInfo(BaseModel):
    """Channel information."""

    id: str = Field(..., description="Channel ID")
    name: str = Field(..., description="Channel name")


class ChannelsResponse(BaseModel):
    """Response model for channels list."""

    channels: list[ChannelInfo] = Field(..., description="List of channels")


class MessageInfo(BaseModel):
    """Message information."""

    id: str = Field(..., description="Message ID")
    content: str = Field(..., description="Message content")
    sender_id: str = Field(..., description="Sender ID")


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""

    metrics: dict[str, Any] = Field(..., description="Telemetry metrics")


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(default="1.0.0", description="Service version")


# Health endpoint
@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint for monitoring service availability."""
    return HealthCheckResponse(
        status="healthy",
        service="AI-Chat Orchestrator Service",
        version="1.0.0",
    )


# Discord endpoints
@router.post("/discord/process", response_model=ProcessMessageResponse)
async def process_discord_message(request: ProcessMessageRequest) -> ProcessMessageResponse:
    """Process a Discord message with AI orchestration."""
    try:
        orchestrator = get_discord_orchestrator()
        response = orchestrator.process_direct(
            channel_id=request.channel_id,
            user_input=request.user_input,
        )

        if response is None:
            raise HTTPException(status_code=500, detail="Failed to process message")

        return ProcessMessageResponse(response=response, success=True)
    except Exception as e:
        logger.exception("Error processing Discord message")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/discord/channels", response_model=ChannelsResponse)
async def get_discord_channels() -> ChannelsResponse:
    """Get list of Discord channels."""
    try:
        orchestrator = get_discord_orchestrator()
        channels = list(orchestrator.chat_client.get_channels())
        return ChannelsResponse(channels=[ChannelInfo(id=ch.id, name=ch.name) for ch in channels])
    except Exception as e:
        logger.exception("Error retrieving Discord channels")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/discord/channels/{channel_id}/messages", response_model=SendMessageResponse)
async def send_discord_message(channel_id: str, request: SendMessageRequest) -> SendMessageResponse:
    """Send a message to a Discord channel."""
    try:
        orchestrator = get_discord_orchestrator()
        success = orchestrator.chat_client.send_message(channel_id, request.content)
        return SendMessageResponse(success=success, message_id=None)
    except Exception as e:
        logger.exception("Error sending Discord message")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/discord/metrics", response_model=MetricsResponse)
async def get_discord_metrics() -> MetricsResponse:
    """Get Discord orchestrator telemetry metrics."""
    try:
        orchestrator = get_discord_orchestrator()
        return MetricsResponse(metrics=orchestrator.get_metrics())
    except Exception as e:
        logger.exception("Error retrieving Discord metrics")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Slack endpoints
@router.post("/slack/process", response_model=ProcessMessageResponse)
async def process_slack_message(request: ProcessMessageRequest) -> ProcessMessageResponse:
    """Process a Slack message with AI orchestration."""
    try:
        orchestrator = get_slack_orchestrator()
        response = orchestrator.process_direct(
            channel_id=request.channel_id,
            user_input=request.user_input,
        )

        if response is None:
            raise HTTPException(status_code=500, detail="Failed to process message")

        return ProcessMessageResponse(response=response, success=True)
    except Exception as e:
        logger.exception("Error processing Slack message")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/slack/channels", response_model=ChannelsResponse)
async def get_slack_channels() -> ChannelsResponse:
    """Get list of Slack channels."""
    try:
        orchestrator = get_slack_orchestrator()
        channels = list(orchestrator.chat_client.get_channels())
        return ChannelsResponse(channels=[ChannelInfo(id=ch.id, name=ch.name) for ch in channels])
    except Exception as e:
        logger.exception("Error retrieving Slack channels")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/slack/channels/{channel_id}/messages", response_model=SendMessageResponse)
async def send_slack_message(channel_id: str, request: SendMessageRequest) -> SendMessageResponse:
    """Send a message to a Slack channel."""
    try:
        orchestrator = get_slack_orchestrator()
        success = orchestrator.chat_client.send_message(channel_id, request.content)
        return SendMessageResponse(success=success, message_id=None)
    except Exception as e:
        logger.exception("Error sending Slack message")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/slack/metrics", response_model=MetricsResponse)
async def get_slack_metrics() -> MetricsResponse:
    """Get Slack orchestrator telemetry metrics."""
    try:
        orchestrator = get_slack_orchestrator()
        return MetricsResponse(metrics=orchestrator.get_metrics())
    except Exception as e:
        logger.exception("Error retrieving Slack metrics")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==================== Ticketing Endpoints ====================


class CreateTicketRequest(BaseModel):
    """Request model for creating a ticket."""

    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    assignee: str | None = Field(None, description="Optional assignee ID")


class TicketResponse(BaseModel):
    """Response model for a ticket."""

    id: str = Field(..., description="Ticket ID")
    title: str = Field(..., description="Ticket title")
    description: str = Field(..., description="Ticket description")
    status: str = Field(..., description="Ticket status")
    assignee: str | None = Field(None, description="Assignee ID")


class TicketListResponse(BaseModel):
    """Response model for a list of tickets."""

    tickets: list[TicketResponse] = Field(..., description="List of tickets")


# Jira Endpoints
@router.post("/jira/tickets", response_model=TicketResponse)
async def create_jira_ticket(request: CreateTicketRequest) -> TicketResponse:
    """Create a new Jira ticket."""
    try:
        client = get_jira_ticket_client()
        ticket = client.create_ticket(
            title=request.title,
            description=request.description,
            assignee=request.assignee,
        )
        return TicketResponse(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status.value,
            assignee=ticket.assignee,
        )
    except Exception as e:
        logger.exception("Error creating Jira ticket")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/jira/tickets/{ticket_id}", response_model=TicketResponse)
async def get_jira_ticket(ticket_id: str) -> TicketResponse:
    """Get a Jira ticket by ID."""
    try:
        client = get_jira_ticket_client()
        ticket = client.get_ticket(ticket_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        return TicketResponse(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status.value,
            assignee=ticket.assignee,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving Jira ticket {ticket_id}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/jira/tickets", response_model=TicketListResponse)
async def search_jira_tickets(query: str | None = None, status: str | None = None) -> TicketListResponse:
    """Search Jira tickets."""
    try:
        client = get_jira_ticket_client()
        ticket_status = TicketStatus(status) if status else None
        tickets = client.search_tickets(query=query, status=ticket_status)
        return TicketListResponse(
            tickets=[
                TicketResponse(
                    id=t.id,
                    title=t.title,
                    description=t.description,
                    status=t.status.value,
                    assignee=t.assignee,
                )
                for t in tickets
            ]
        )
    except Exception as e:
        logger.exception("Error searching Jira tickets")
        raise HTTPException(status_code=500, detail=str(e)) from e


# Google Tasks Endpoints
@router.post("/gtasks/tickets", response_model=TicketResponse)
async def create_gtasks_ticket(request: CreateTicketRequest) -> TicketResponse:
    """Create a new Google Tasks ticket."""
    try:
        client = get_gtasks_ticket_client()
        ticket = client.create_ticket(
            title=request.title,
            description=request.description,
            assignee=request.assignee,
        )
        return TicketResponse(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status.value,
            assignee=ticket.assignee,
        )
    except Exception as e:
        logger.exception("Error creating Google Tasks ticket")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/gtasks/tickets/{ticket_id}", response_model=TicketResponse)
async def get_gtasks_ticket(ticket_id: str) -> TicketResponse:
    """Get a Google Tasks ticket by ID."""
    try:
        client = get_gtasks_ticket_client()
        ticket = client.get_ticket(ticket_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        return TicketResponse(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status.value,
            assignee=ticket.assignee,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving Google Tasks ticket {ticket_id}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/gtasks/tickets", response_model=TicketListResponse)
async def search_gtasks_tickets(query: str | None = None, status: str | None = None) -> TicketListResponse:
    """Search Google Tasks tickets."""
    try:
        client = get_gtasks_ticket_client()
        ticket_status = TicketStatus(status) if status else None
        tickets = client.search_tickets(query=query, status=ticket_status)
        return TicketListResponse(
            tickets=[
                TicketResponse(
                    id=t.id,
                    title=t.title,
                    description=t.description,
                    status=t.status.value,
                    assignee=t.assignee,
                )
                for t in tickets
            ]
        )
    except Exception as e:
        logger.exception("Error searching Google Tasks tickets")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==================== Slack Webhook Endpoint ====================


class SlackEventRequest(BaseModel):
    """Slack Event API request model."""

    type: str = Field(..., description="Event type")
    challenge: str | None = Field(None, description="Challenge for URL verification")
    event: dict[str, Any] | None = Field(None, description="Event data")


@router.post("/webhook/slack")
async def slack_webhook(request: SlackEventRequest) -> dict[str, Any]:
    """Handle incoming Slack events.

    This endpoint handles:
    1. URL verification challenge from Slack
    2. Message events from channels where the bot is present
    """
    try:
        # Handle URL verification challenge
        if request.type == "url_verification":
            logger.info("Received Slack URL verification challenge")
            if request.challenge:
                return {"challenge": request.challenge}
            raise HTTPException(status_code=400, detail="Challenge missing from verification request")

        # Handle message events
        if request.type == "event_callback" and request.event:
            event = request.event
            event_type = event.get("type")

            # Only process message events in channels (not DMs, not bot messages)
            if event_type == "message" and event.get("channel_type") == "channel":
                # Ignore bot messages to prevent loops
                if event.get("bot_id") or event.get("subtype") == "bot_message":
                    logger.debug("Ignoring bot message to prevent loop")
                    return {"ok": True}

                channel_id = event.get("channel")
                user_input = event.get("text", "")

                if channel_id and user_input:
                    logger.info(f"Processing Slack message from channel {channel_id}: {user_input[:50]}...")

                    # Process the message through orchestrator
                    orchestrator = get_slack_orchestrator()
                    response = orchestrator.process_direct(
                        channel_id=channel_id,
                        user_input=user_input,
                    )

                    if response:
                        logger.info(f"AI response sent to Slack channel {channel_id}")
                    else:
                        logger.error("Failed to get AI response")

        return {"ok": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing Slack webhook")
        # Return 200 to acknowledge receipt even on error (Slack retries otherwise)
        return {"ok": False, "error": str(e)}
