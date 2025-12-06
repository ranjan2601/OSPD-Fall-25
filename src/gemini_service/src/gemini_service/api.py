"""FastAPI routes for Gemini AI chat service.

This module defines the API endpoints for the shared AI Service interface.
"""

import logging
from typing import Any

from ai_client_api.credential import resolve_api_key
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import ai_client_api
import gemini_client_impl

gemini_client_impl.register()

logger = logging.getLogger(__name__)

router = APIRouter()


class ToolDefinition(BaseModel):
    """Definition of a tool the AI can call."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="What the tool does")
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for tool parameters",
    )


class SendMessageRequest(BaseModel):
    """Request model for sending a message to the AI."""

    user_id: str = Field(..., description="Unique identifier for the user")
    prompt: str = Field(..., description="The user's message/prompt text")
    tools: list[ToolDefinition] | None = Field(
        default=None,
        description="Optional list of tool definitions",
    )


class SendMessageResponse(BaseModel):
    """Response model from the AI service."""

    text: str = Field(..., description="The AI's response text")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of tool calls from the response",
    )


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(default="1.0.0", description="Service version")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint for monitoring service availability."""
    return HealthCheckResponse(
        status="healthy",
        service="Gemini AI Service",
        version="1.0.0",
    )


@router.post("/send_message", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest) -> SendMessageResponse:
    """Send a message to the AI and receive a response."""
    if not request.user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    if not request.prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    try:
        api_key = resolve_api_key(
            user_id=request.user_id,
            provider="gemini",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        ) from e

    try:
        context: dict[str, Any] | None = None
        if request.tools:
            context = {"tools": [tool.model_dump() for tool in request.tools]}

        service = ai_client_api.get_client(
            user_id=request.user_id,
            api_key=api_key,
        )

        response_text = service.send_message(
            user_id=request.user_id,
            prompt=request.prompt,
            context=context,
        )

        tool_calls = service.extract_tool_calls(response_text)

        return SendMessageResponse(
            text=response_text,
            tool_calls=[
                {
                    "tool_name": tc.tool_name,
                    "tool_args": tc.tool_args,
                    "tool_id": tc.tool_id,
                }
                for tc in tool_calls
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error sending message")
        raise HTTPException(
            status_code=500,
            detail=f"Error sending message: {e!s}",
        ) from e
