"""Main FastAPI application for AI-Chat Orchestrator Service.

This module initializes and configures the FastAPI application,
loads environment variables, and sets up all API routes.
"""

import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from .api import router
from .auth_router import router as auth_router
from .discord_bot import start_discord_bot

env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

logger = logging.getLogger(__name__)

# Global task for Discord bot
_discord_task: asyncio.Task[None] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - start/stop Discord bot."""
    global _discord_task

    # Startup: Start Discord bot if token is configured
    discord_token = os.getenv("DISCORD_BOT_TOKEN")
    if discord_token:
        logger.info("Starting Discord bot...")
        try:
            _discord_task = asyncio.create_task(start_discord_bot())
            logger.info("✓ Discord bot started successfully")
        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
    else:
        logger.warning("DISCORD_BOT_TOKEN not set - Discord bot will not start")

    yield

    # Shutdown: Stop Discord bot
    if _discord_task:
        logger.info("Stopping Discord bot...")
        _discord_task.cancel()
        try:
            await _discord_task
        except asyncio.CancelledError:
            pass
        logger.info("Discord bot stopped")


app = FastAPI(
    title="AI-Chat Orchestrator Service",
    description="FastAPI service orchestrating AI and Chat platform integrations with Discord Gateway bot",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)
app.include_router(auth_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint returning service status."""
    return {"message": "AI-Chat Orchestrator Service is running (with Discord Gateway bot)"}
