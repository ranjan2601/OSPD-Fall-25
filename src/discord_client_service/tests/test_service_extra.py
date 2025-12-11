"""Extra tests for service module (lifespan and openapi)."""

import asyncio

import pytest

from discord_client_service import service


def test_get_openapi_schema() -> None:
    """Ensure the service exposes a valid OpenAPI schema dict."""
    schema = service.get_openapi_schema()
    assert isinstance(schema, dict)
    assert "openapi" in schema


@pytest.mark.asyncio
async def test_lifespan_context_runs() -> None:
    """Verify the service lifespan async context manager runs without error."""
    # ensure the async context manager runs without error
    async with service.lifespan(service.app):
        # inside lifespan nothing specific to assert; just ensure no exceptions
        await asyncio.sleep(0)
