"""End-to-end tests for orchestrator service API endpoints.

These tests verify the complete user flow:
1. User Input (Chat)
2. Routing/Reasoning (AI)
3. Response (Back to Chat)
"""

import os
from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest

pytestmark = pytest.mark.e2e

SERVICE_URL = os.getenv("ORCHESTRATOR_SERVICE_URL", "http://127.0.0.1:8000")
TIMEOUT = 10.0


@pytest.fixture
def check_service() -> None:
    """Check if orchestrator service is available."""
    try:
        response = httpx.get(f"{SERVICE_URL}/health", timeout=2.0)
        if response.status_code != 200:
            pytest.skip(f"Orchestrator service not available at {SERVICE_URL}")
    except (httpx.ConnectError, httpx.TimeoutException):
        pytest.skip(
            f"Orchestrator service not running at {SERVICE_URL}. "
            "Start with: uv run uvicorn orchestrator_service.main:app"
        )


@pytest.fixture
def http_client() -> httpx.Client:
    """Create HTTP client for API calls."""
    return httpx.Client(base_url=SERVICE_URL, timeout=TIMEOUT)


class TestOrchestratorE2EHealthCheck:
    """Test orchestrator service health and status endpoints."""

    def test_health_endpoint(self, check_service: Any, http_client: Any) -> None:
        """Verify health endpoint returns 200."""
        response = http_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self, check_service: Any, http_client: Any) -> None:
        """Verify root endpoint is accessible."""
        response = http_client.get("/")
        assert response.status_code == 200


class TestDiscordOrchestrationE2E:
    """Test Discord chat integration E2E flow."""

    @patch("orchestrator_service.api.get_discord_orchestrator")
    def test_discord_process_message(
        self,
        mock_get_orch: Any,
        check_service: Any,
        http_client: Any,
    ) -> None:
        """Test complete Discord message processing flow."""
        # Mock orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.handle_message.return_value = True
        mock_get_orch.return_value = mock_orchestrator

        response = http_client.post(
            "/discord/process",
            json={
                "channel_id": "123456789",
                "user_input": "What is AI?",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "channel_id" in data

    @patch("orchestrator_service.api.get_discord_orchestrator")
    def test_discord_get_metrics(
        self,
        mock_get_orch: Any,
        check_service: Any,
        http_client: Any,
    ) -> None:
        """Test Discord metrics endpoint."""
        mock_orchestrator = Mock()
        mock_orchestrator.get_metrics.return_value = {
            "total_requests": 10,
            "successful_requests": 8,
            "failed_requests": 2,
            "success_rate": 0.8,
            "average_latency_seconds": 0.5,
        }
        mock_get_orch.return_value = mock_orchestrator

        response = http_client.get("/discord/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "success_rate" in data
        assert data["total_requests"] == 10


class TestSlackOrchestrationE2E:
    """Test Slack chat integration E2E flow."""

    @patch("orchestrator_service.api.get_slack_orchestrator")
    def test_slack_process_message(
        self,
        mock_get_orch: Any,
        check_service: Any,
        http_client: Any,
    ) -> None:
        """Test complete Slack message processing flow."""
        mock_orchestrator = Mock()
        mock_orchestrator.handle_message.return_value = True
        mock_get_orch.return_value = mock_orchestrator

        response = http_client.post(
            "/slack/process",
            json={
                "channel_id": "C123456",
                "user_input": "Hello AI",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("orchestrator_service.api.get_slack_orchestrator")
    def test_slack_get_metrics(
        self,
        mock_get_orch: Any,
        check_service: Any,
        http_client: Any,
    ) -> None:
        """Test Slack metrics endpoint."""
        mock_orchestrator = Mock()
        mock_orchestrator.get_metrics.return_value = {
            "total_requests": 5,
            "successful_requests": 5,
            "failed_requests": 0,
            "success_rate": 1.0,
        }
        mock_get_orch.return_value = mock_orchestrator

        response = http_client.get("/slack/metrics")

        assert response.status_code == 200
        data = response.json()
        assert data["success_rate"] == 1.0


class TestProviderSwappingE2E:
    """Test provider swapping capability E2E."""

    @patch("orchestrator_service.api.get_discord_orchestrator")
    @patch("orchestrator_service.api.get_slack_orchestrator")
    def test_same_request_different_providers(
        self,
        mock_slack: Any,
        mock_discord: Any,
        check_service: Any,
        http_client: Any,
    ) -> None:
        """Verify same request works with both Discord and Slack."""
        # Setup mock orchestrators
        mock_discord_orch = Mock()
        mock_discord_orch.handle_message.return_value = True
        mock_discord.return_value = mock_discord_orch

        mock_slack_orch = Mock()
        mock_slack_orch.handle_message.return_value = True
        mock_slack.return_value = mock_slack_orch

        test_input = "What is machine learning?"

        # Send to Discord
        discord_response = http_client.post(
            "/discord/process",
            json={"channel_id": "discord_ch", "user_input": test_input},
        )

        # Send to Slack
        slack_response = http_client.post(
            "/slack/process",
            json={"channel_id": "slack_ch", "user_input": test_input},
        )

        # Both should succeed
        assert discord_response.status_code == 200
        assert slack_response.status_code == 200
        assert discord_response.json()["success"] is True
        assert slack_response.json()["success"] is True


class TestErrorHandlingE2E:
    """Test error handling in E2E flows."""

    @patch("orchestrator_service.api.get_discord_orchestrator")
    def test_invalid_request_returns_400(
        self,
        mock_get_orch: Any,
        check_service: Any,
        http_client: Any,
    ) -> None:
        """Test that invalid requests return 400."""
        mock_orchestrator = Mock()
        mock_get_orch.return_value = mock_orchestrator

        response = http_client.post(
            "/discord/process",
            json={
                "channel_id": "",  # Empty channel ID
                "user_input": "Test",
            },
        )

        assert response.status_code == 400

    @patch("orchestrator_service.api.get_discord_orchestrator")
    def test_orchestrator_failure_handled(
        self,
        mock_get_orch: Any,
        check_service: Any,
        http_client: Any,
    ) -> None:
        """Test that orchestrator failures are handled gracefully."""
        mock_orchestrator = Mock()
        mock_orchestrator.handle_message.return_value = False  # Simulate failure
        mock_get_orch.return_value = mock_orchestrator

        response = http_client.post(
            "/discord/process",
            json={
                "channel_id": "123",
                "user_input": "Test",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False


class TestTelemetryE2E:
    """Test telemetry and monitoring E2E."""

    @patch("orchestrator_service.api.get_discord_orchestrator")
    def test_metrics_tracked_across_requests(
        self,
        mock_get_orch: Any,
        check_service: Any,
        http_client: Any,
    ) -> None:
        """Verify metrics are tracked across multiple requests."""
        mock_orchestrator = Mock()
        mock_orchestrator.handle_message.return_value = True

        # Simulate increasing metrics
        call_count = [0]

        def mock_get_metrics() -> dict[str, Any]:
            call_count[0] += 1
            return {
                "total_requests": call_count[0],
                "successful_requests": call_count[0],
                "failed_requests": 0,
                "success_rate": 1.0,
                "average_latency_seconds": 0.1 * call_count[0],
            }

        mock_orchestrator.get_metrics = mock_get_metrics
        mock_get_orch.return_value = mock_orchestrator

        # Make multiple requests
        for i in range(3):
            http_client.post(
                "/discord/process",
                json={"channel_id": f"ch{i}", "user_input": f"Test {i}"},
            )

        # Check final metrics
        response = http_client.get("/discord/metrics")
        data = response.json()

        assert data["total_requests"] >= 3
        assert data["average_latency_seconds"] > 0

