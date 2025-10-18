"""Mail Client Service - FastAPI service exposing mail client functionality.

This package contains the FastAPI application that exposes mail client
operations over HTTP REST API.
"""

__all__ = ["app"]

from .main import app
