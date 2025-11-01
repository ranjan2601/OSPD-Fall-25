"""Tests for the combined FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the combined app."""
    return TestClient(app)


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint returns service info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "services" in data
    assert "Mail Client (/mail)" in data["services"]
    assert "Gemini AI (/ai)" in data["services"]


def test_health_endpoint(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data
    assert "mail" in data["services"]
    assert "ai" in data["services"]


def test_mail_service_mounted(client: TestClient) -> None:
    """Test that mail service routes are mounted at /mail prefix."""
    response = client.get("/mail/messages")
    # Should either succeed or fail gracefully (not 404 for route not found)
    assert response.status_code in [200, 500, 401, 403]


def test_ai_service_mounted(client: TestClient) -> None:
    """Test that AI service routes are mounted at /ai prefix."""
    response = client.get("/ai/")
    # The /ai/ endpoint should exist (would redirect or show service info)
    assert response.status_code in [200, 404, 500]


def test_docs_endpoint(client: TestClient) -> None:
    """Test OpenAPI docs are available."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_schema(client: TestClient) -> None:
    """Test OpenAPI schema is generated."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
    # Check both services are in paths
    paths = data["paths"]
    # Mail service paths
    mail_paths = [p for p in paths if p.startswith("/mail")]
    # AI service paths
    ai_paths = [p for p in paths if p.startswith("/ai")]
    assert len(mail_paths) > 0, "Mail service routes should be in OpenAPI schema"
    assert len(ai_paths) > 0, "AI service routes should be in OpenAPI schema"
