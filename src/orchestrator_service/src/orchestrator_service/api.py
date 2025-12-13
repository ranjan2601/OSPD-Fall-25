"""FastAPI routes for AI-Chat Orchestrator service."""

import logging
import os
from typing import Any

from ai_chat_orchestrator.factory import (
    create_gemini_discord_orchestrator,
    create_gemini_slack_orchestrator,
)
from ai_client_api.credential import resolve_api_key
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import gemini_client_impl

gemini_client_impl.register()

logger = logging.getLogger(__name__)

router = APIRouter()

# Global orchestrator instances for different providers
_discord_orchestrator: Any = None
_slack_orchestrator: Any = None


def get_discord_orchestrator() -> Any:
    """Get or create the Discord orchestrator instance."""
    global _discord_orchestrator
    if _discord_orchestrator is None:
        try:
            gemini_api_key = resolve_api_key(user_id="service", provider="gemini")
            _discord_orchestrator = create_gemini_discord_orchestrator(
                gemini_api_key=gemini_api_key,
                system_prompt="You are a helpful AI assistant in a Discord channel.",
            )
            logger.info("Discord orchestrator initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize Discord orchestrator: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
    return _discord_orchestrator


def get_slack_orchestrator() -> Any:
    """Get or create the Slack orchestrator instance."""
    global _slack_orchestrator
    if _slack_orchestrator is None:
        try:
            gemini_api_key = resolve_api_key(user_id="service", provider="gemini")
            slack_token = os.getenv("SLACK_BOT_TOKEN", "")
            slack_base_url = os.getenv("SLACK_BASE_URL", "https://slack.com/api")

            _slack_orchestrator = create_gemini_slack_orchestrator(
                gemini_api_key=gemini_api_key,
                slack_token=slack_token,
                slack_base_url=slack_base_url,
                system_prompt="You are a helpful AI assistant in a Slack channel.",
            )
            logger.info("Slack orchestrator initialized successfully")
        except ValueError as e:
            logger.error(f"Failed to initialize Slack orchestrator: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e
    return _slack_orchestrator


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
