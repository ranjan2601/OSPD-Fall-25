"""FastAPI routes for Gemini AI service aligned with OSS-APIs standard.

This module defines the API endpoints for the shared AIInterface,
supporting both conversational and structured output modes.
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


class GenerateResponseRequest(BaseModel):
    """Request model for generating a response from the AI."""

    user_input: str = Field(..., description="The user's input/prompt text")
    system_prompt: str = Field(..., description="System instruction for the model")
    response_schema: dict[str, Any] | None = Field(
        default=None,
        description="Optional JSON schema for structured output",
    )


class GenerateResponseResponse(BaseModel):
    """Response model from the AI service."""

    output: str | dict[str, Any] = Field(
        ...,
        description="The AI's response (string for conversational, dict for structured)",
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


@router.post("/generate", response_model=GenerateResponseResponse)
async def generate_response(request: GenerateResponseRequest) -> GenerateResponseResponse:
    """Generate a response from the AI with optional structured output.

    Supports:
    - Conversational mode: user_input + system_prompt, no schema
    - Structured output mode: user_input + system_prompt + response_schema
    """
    if not request.user_input:
        raise HTTPException(status_code=400, detail="user_input is required")
    if not request.system_prompt:
        raise HTTPException(status_code=400, detail="system_prompt is required")

    try:
        api_key = resolve_api_key(user_id="service", provider="gemini")
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        ) from e

    try:
        service = ai_client_api.get_client(api_key=api_key)

        output = service.generate_response(
            user_input=request.user_input,
            system_prompt=request.system_prompt,
            response_schema=request.response_schema,
        )

        return GenerateResponseResponse(output=output)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        logger.exception("Error generating response")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {e!s}",
        ) from e
