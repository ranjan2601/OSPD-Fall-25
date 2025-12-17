"""Coverage tests for the combined FastAPI app."""

import sys
from types import ModuleType

from fastapi.testclient import TestClient


def test_root_and_health_endpoints() -> None:
    # Some environments do not ship the mail client service package.
    # Stub it so importing `app` works consistently.
    if "mail_client_service" not in sys.modules:
        from fastapi import APIRouter

        svc = ModuleType("mail_client_service")
        api = ModuleType("mail_client_service.api")
        api.router = APIRouter()
        sys.modules["mail_client_service"] = svc
        sys.modules["mail_client_service.api"] = api

    from app import app

    client = TestClient(app)

    root = client.get("/")
    assert root.status_code == 200
    payload = root.json()
    assert payload["message"]
    assert "services" in payload

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


