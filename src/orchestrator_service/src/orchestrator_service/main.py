"""Main FastAPI application for AI-Chat Orchestrator Service.

This module initializes and configures the FastAPI application,
loads environment variables, and sets up all API routes.
"""

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from .api import router

env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

app = FastAPI(
    title="AI-Chat Orchestrator Service",
    description="FastAPI service orchestrating AI and Chat platform integrations",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint returning service status."""
    return {"message": "AI-Chat Orchestrator Service is running"}
