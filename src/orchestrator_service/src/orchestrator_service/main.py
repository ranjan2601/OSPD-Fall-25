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

from .api import get_discord_orchestrator, get_slack_orchestrator, router
from .auth_router import router as auth_router
from .discord_bot import start_discord_bot
from .metrics_exporter import get_metrics_exporter

env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

_discord_task: asyncio.Task[None] | None = None
_metrics_task: asyncio.Task[None] | None = None


async def export_metrics_periodically() -> None:
    """Background task to export metrics to Cloud Monitoring every 60 seconds."""
    exporter = get_metrics_exporter()
    logger.info("Starting metrics export background task")

    while True:
        try:
            await asyncio.sleep(60)

            try:
                aggregated_metrics = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "success_rate": 0.0,
                    "failure_rate": 0.0,
                    "average_latency_seconds": 0.0,
                }

                discord_latency = 0.0
                discord_requests = 0
                slack_latency = 0.0
                slack_requests = 0

                try:
                    discord_orch = get_discord_orchestrator()
                    discord_metrics = discord_orch.get_metrics()
                    aggregated_metrics["total_requests"] += discord_metrics.get("total_requests", 0)
                    aggregated_metrics["successful_requests"] += discord_metrics.get("successful_requests", 0)
                    aggregated_metrics["failed_requests"] += discord_metrics.get("failed_requests", 0)
                    discord_latency = discord_metrics.get("average_latency_seconds", 0.0)
                    discord_requests = discord_metrics.get("total_requests", 0)
                except Exception as e:
                    logger.debug(f"Could not get Discord metrics: {e}")

                try:
                    slack_orch = get_slack_orchestrator()
                    slack_metrics = slack_orch.get_metrics()
                    aggregated_metrics["total_requests"] += slack_metrics.get("total_requests", 0)
                    aggregated_metrics["successful_requests"] += slack_metrics.get("successful_requests", 0)
                    aggregated_metrics["failed_requests"] += slack_metrics.get("failed_requests", 0)
                    slack_latency = slack_metrics.get("average_latency_seconds", 0.0)
                    slack_requests = slack_metrics.get("total_requests", 0)
                except Exception as e:
                    logger.debug(f"Could not get Slack metrics: {e}")

                total = aggregated_metrics["total_requests"]
                if total > 0:
                    aggregated_metrics["success_rate"] = aggregated_metrics["successful_requests"] / total
                    aggregated_metrics["failure_rate"] = aggregated_metrics["failed_requests"] / total

                    total_latency = (discord_latency * discord_requests) + (slack_latency * slack_requests)
                    aggregated_metrics["average_latency_seconds"] = total_latency / total

                exporter.export_metrics(aggregated_metrics)
                logger.debug(f"Exported aggregated metrics: {aggregated_metrics}")
            except Exception as e:
                logger.error(f"Error getting/exporting metrics: {e}")

        except asyncio.CancelledError:
            logger.info("Metrics export task cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in metrics export: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - start/stop Discord bot and metrics export."""
    global _discord_task, _metrics_task

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

    logger.info("Starting metrics export background task...")
    try:
        _metrics_task = asyncio.create_task(export_metrics_periodically())
        logger.info("✓ Metrics export task started successfully")
    except Exception as e:
        logger.error(f"Failed to start metrics export task: {e}")

    yield

    if _metrics_task:
        logger.info("Stopping metrics export task...")
        _metrics_task.cancel()
        try:
            await _metrics_task
        except asyncio.CancelledError:
            pass
        logger.info("Metrics export task stopped")

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
