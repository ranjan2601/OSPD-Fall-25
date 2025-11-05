"""Main FastAPI application for mail client service.

This module initializes and configures the FastAPI application,
and sets up all API routes for mail client operations.
"""

from fastapi import FastAPI

from .api import router

app = FastAPI(
    title="Mail Client Service",
    description="FastAPI service for mail client operations",
    version="0.1.0",
)
app.include_router(router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint returning service status."""
    return {"message": "Mail Client Service is running"}
