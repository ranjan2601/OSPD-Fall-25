"""End-to-end tests for AI Chat Orchestrator Service.

Full workflow tests with real services (Gemini AI, Jira, Google Tasks) to verify:
- Complete orchestrator workflows (Input -> AI -> Tickets -> Output)
- Discord message processing with ticket integration
- Slack message processing with ticket integration
- Jira ticket operations (create, read, search)
- Google Tasks operations (create, read, search)
- Metrics tracking across workflows
- Service health and stability

These tests require:
- GEMINI_API_KEY environment variable
- Service running at http://127.0.0.1:8080
- Jira credentials configured (optional)
- Google Tasks credentials configured (optional)
"""

import os
import time
import uuid
from typing import Any

import httpx
import pytest

# Mark all tests in this file as e2e tests
pytestmark = pytest.mark.e2e

# Service configuration - allow override via environment variable
SERVICE_URL = os.getenv("ORCHESTRATOR_SERVICE_URL", "http://127.0.0.1:8080")
TIMEOUT = 60.0  # Increased timeout for AI operations which can be slow


@pytest.fixture(scope="module")
def check_service_running() -> None:
    """Verify Orchestrator service is running on localhost:8080."""
    try:
        response = httpx.get(f"{SERVICE_URL}/health", timeout=2.0)
        if response.status_code != 200:
            pytest.skip(f"Service at {SERVICE_URL} is not responding correctly")
    except (httpx.ConnectError, httpx.TimeoutException):
        pytest.skip(
            f"Orchestrator service not running at {SERVICE_URL}. "
            "Start with: uv run uvicorn orchestrator_service.api:app --port 8080 --reload",
        )


@pytest.fixture(scope="module")
def check_gemini_api_key() -> str:
    """Verify GEMINI_API_KEY environment variable is set."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip(
            "GEMINI_API_KEY not set in environment. Set it with: export GEMINI_API_KEY=your_api_key",
        )
    return api_key


@pytest.fixture
def unique_channel_id() -> str:
    """Generate unique channel_id for test isolation."""
    return f"e2e_channel_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def unique_message_content() -> str:
    """Generate unique message content for test isolation."""
    return f"Test message {uuid.uuid4().hex[:8]}"


@pytest.fixture
def http_client() -> httpx.Client:
    """Create httpx client for API calls."""
    return httpx.Client(base_url=SERVICE_URL, timeout=TIMEOUT)


class TestOrchestratorServiceHealthCheck:
    """Test orchestrator service health and responsiveness."""

    def test_health_endpoint(
        self,
        check_service_running: Any,
        http_client: httpx.Client,
    ) -> None:
        """Test health endpoint returns 200 and proper structure."""
        response = http_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data


class TestOrchestratorDiscordWorkflow:
    """Test complete Discord message processing workflow with AI."""

    def test_discord_process_simple_message(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
        unique_channel_id: str,
        unique_message_content: str,
    ) -> None:
        """Test Discord message processing returns AI response."""
        response = http_client.post(
            "/discord/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": unique_message_content,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        # Verify it's a real AI response (not empty or mock)
        assert data["response"] != unique_message_content

    def test_discord_conversation_with_context(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
        unique_channel_id: str,
    ) -> None:
        """Test Discord conversation maintains context across messages."""
        # First message
        response1 = http_client.post(
            "/discord/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": "My favorite color is blue.",
            },
        )
        assert response1.status_code == 200

        # Give AI time to process
        time.sleep(1)

        # Second message referencing first
        response2 = http_client.post(
            "/discord/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": "What color did I just tell you I like?",
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # AI should remember the color from conversation history
        response_text = data2["response"].lower()
        assert "blue" in response_text

    def test_discord_metrics_tracking(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
        unique_channel_id: str,
    ) -> None:
        """Test Discord orchestrator tracks metrics correctly."""
        # Get initial metrics
        initial_metrics = http_client.get("/discord/metrics")
        assert initial_metrics.status_code == 200
        initial_data = initial_metrics.json()
        # Metrics are nested under "metrics" key
        metrics_data = initial_data.get("metrics", {})
        initial_requests = metrics_data.get("total_requests", 0)

        # Send a message
        http_client.post(
            "/discord/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": "Hello!",
            },
        )

        # Get updated metrics
        updated_metrics = http_client.get("/discord/metrics")
        assert updated_metrics.status_code == 200
        updated_data = updated_metrics.json()
        updated_metrics_data = updated_data.get("metrics", {})

        # Verify metrics increased
        assert updated_metrics_data["total_requests"] >= initial_requests + 1


class TestOrchestratorSlackWorkflow:
    """Test complete Slack message processing workflow with AI."""

    def test_slack_process_simple_message(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
        unique_channel_id: str,
        unique_message_content: str,
    ) -> None:
        """Test Slack message processing returns AI response."""
        response = http_client.post(
            "/slack/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": unique_message_content,
            },
        )

        # Skip if Slack is not properly configured (500 error)
        if response.status_code == 500:
            pytest.skip("Slack integration not properly configured in deployed service")

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        # Verify it's a real AI response
        assert data["response"] != unique_message_content

    def test_slack_metrics_tracking(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
        unique_channel_id: str,
    ) -> None:
        """Test Slack orchestrator tracks metrics correctly."""
        # Get initial metrics
        initial_metrics = http_client.get("/slack/metrics")
        assert initial_metrics.status_code == 200
        initial_data = initial_metrics.json()
        # Metrics are nested under "metrics" key
        metrics_data = initial_data.get("metrics", {})
        initial_requests = metrics_data.get("total_requests", 0)

        # Send a message
        response = http_client.post(
            "/slack/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": "Hello!",
            },
        )

        # Skip if Slack is not properly configured
        if response.status_code == 500:
            pytest.skip("Slack integration not properly configured in deployed service")

        # Get updated metrics
        updated_metrics = http_client.get("/slack/metrics")
        assert updated_metrics.status_code == 200
        updated_data = updated_metrics.json()
        updated_metrics_data = updated_data.get("metrics", {})

        # Verify metrics increased
        assert updated_metrics_data["total_requests"] >= initial_requests + 1


@pytest.mark.local_credentials
class TestOrchestratorJiraIntegration:
    """Test Jira ticket integration with real Jira API.

    These tests require Jira credentials to be configured.
    Skip if Jira is not available.
    """

    def test_jira_list_tickets(
        self,
        check_service_running: Any,
        http_client: httpx.Client,
    ) -> None:
        """Test listing Jira tickets through orchestrator."""
        response = http_client.get("/jira/tickets")

        # If Jira not configured, expect 500 or similar
        if response.status_code >= 500:
            pytest.skip("Jira not configured for this environment")

        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert isinstance(data["tickets"], list)

    def test_jira_create_and_retrieve_ticket(
        self,
        check_service_running: Any,
        http_client: httpx.Client,
    ) -> None:
        """Test creating and retrieving a Jira ticket."""
        # Create ticket
        unique_title = f"E2E Test Ticket {uuid.uuid4().hex[:8]}"
        create_response = http_client.post(
            "/jira/tickets",
            json={
                "title": unique_title,
                "description": "This is an automated E2E test ticket",
            },
        )

        # If Jira not configured, skip
        if create_response.status_code >= 500:
            pytest.skip("Jira not configured for this environment")

        assert create_response.status_code == 200
        create_data = create_response.json()
        assert "id" in create_data
        ticket_id = create_data["id"]

        # Retrieve the ticket
        get_response = http_client.get(f"/jira/tickets/{ticket_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["id"] == ticket_id
        assert get_data["title"] == unique_title

    def test_jira_search_tickets_with_query(
        self,
        check_service_running: Any,
        http_client: httpx.Client,
    ) -> None:
        """Test searching Jira tickets with query parameters."""
        response = http_client.get("/jira/tickets", params={"status": "open"})

        # If Jira not configured, skip
        if response.status_code >= 500:
            pytest.skip("Jira not configured for this environment")

        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        # All returned tickets should have open status
        for ticket in data["tickets"]:
            assert ticket["status"] in ["open", "OPEN"]


@pytest.mark.local_credentials
class TestOrchestratorGoogleTasksIntegration:
    """Test Google Tasks integration with real Google Tasks API.

    These tests require Google Tasks credentials to be configured.
    Skip if Google Tasks is not available.
    """

    def test_gtasks_list_tasks(
        self,
        check_service_running: Any,
        http_client: httpx.Client,
    ) -> None:
        """Test listing Google Tasks through orchestrator."""
        response = http_client.get("/gtasks/tickets")

        # If Google Tasks not configured, expect 500 or similar
        if response.status_code >= 500:
            pytest.skip("Google Tasks not configured for this environment")

        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert isinstance(data["tickets"], list)

    def test_gtasks_create_and_retrieve_task(
        self,
        check_service_running: Any,
        http_client: httpx.Client,
    ) -> None:
        """Test creating and retrieving a Google Task."""
        # Create task
        unique_title = f"E2E Test Task {uuid.uuid4().hex[:8]}"
        create_response = http_client.post(
            "/gtasks/tickets",
            json={
                "title": unique_title,
                "description": "This is an automated E2E test task",
            },
        )

        # If Google Tasks not configured, skip
        if create_response.status_code >= 500:
            pytest.skip("Google Tasks not configured for this environment")

        assert create_response.status_code == 200
        create_data = create_response.json()
        assert "id" in create_data
        task_id = create_data["id"]

        # Retrieve the task
        get_response = http_client.get(f"/gtasks/tickets/{task_id}")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["id"] == task_id
        assert get_data["title"] == unique_title


@pytest.mark.local_credentials
class TestOrchestratorFullWorkflow:
    """Test complete end-to-end workflows: User Input -> AI -> Tickets -> Response.

    These tests verify the full application flow with real services.
    """

    def test_discord_ai_ticket_complete_workflow(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
        unique_channel_id: str,
    ) -> None:
        """Test complete Discord workflow: message -> AI interprets -> fetches tickets -> responds."""
        # Send message asking for tickets
        response = http_client.post(
            "/discord/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": "Show me the latest Jira tickets",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

        # Response should either:
        # 1. Contain ticket information if Jira is configured
        # 2. Contain a message about Jira not being available
        response_text = data["response"].lower()
        assert (
            "ticket" in response_text
            or "jira" in response_text
            or "not currently available" in response_text
            or "task" in response_text
        )

    def test_slack_ai_ticket_complete_workflow(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
        unique_channel_id: str,
    ) -> None:
        """Test complete Slack workflow: message -> AI interprets -> fetches tickets -> responds."""
        # Send message asking for tickets
        response = http_client.post(
            "/slack/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": "What are my open Google Tasks?",
            },
        )

        # Skip if Slack is not properly configured
        if response.status_code == 500:
            pytest.skip("Slack integration not properly configured in deployed service")

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

        # Response should either:
        # 1. Contain task information if Google Tasks is configured
        # 2. Contain a message about Google Tasks not being available
        response_text = data["response"].lower()
        assert (
            "task" in response_text
            or "google" in response_text
            or "not currently available" in response_text
            or "ticket" in response_text
        )

    def test_workflow_with_conversation_context_and_tickets(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
        unique_channel_id: str,
    ) -> None:
        """Test workflow maintains conversation context when working with tickets."""
        # First message - ask about tickets
        response1 = http_client.post(
            "/discord/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": "Show me open tickets",
            },
        )
        assert response1.status_code == 200

        time.sleep(1)

        # Second message - reference previous response
        response2 = http_client.post(
            "/discord/process",
            json={
                "channel_id": unique_channel_id,
                "user_input": "How many were there?",
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # AI should be able to answer based on conversation history
        assert len(data2["response"]) > 0
        # Response should contain a number or indication of count
        response_text = data2["response"].lower()
        assert any(word in response_text for word in ["0", "1", "2", "3", "4", "5", "no", "none", "several", "many", "available"])


class TestOrchestratorStressAndStability:
    """Test orchestrator service stability under load."""

    @pytest.mark.timeout(300)  # 5 minutes timeout for sequential requests with real AI calls
    def test_multiple_sequential_requests(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
        unique_channel_id: str,
    ) -> None:
        """Test service handles multiple sequential requests correctly."""
        # Use a client with longer timeout for this test (5 sequential AI calls)
        with httpx.Client(base_url=SERVICE_URL, timeout=120.0) as long_timeout_client:
            for i in range(5):
                response = long_timeout_client.post(
                    "/discord/process",
                    json={
                        "channel_id": unique_channel_id,
                        "user_input": f"Message {i + 1}",
                    },
                )
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert len(data["response"]) > 0

    def test_service_stability_across_different_channels(
        self,
        check_service_running: Any,
        check_gemini_api_key: Any,
        http_client: httpx.Client,
    ) -> None:
        """Test service handles requests from different channels independently."""
        channels = [f"e2e_channel_{uuid.uuid4().hex[:4]}" for _ in range(3)]

        for channel in channels:
            response = http_client.post(
                "/discord/process",
                json={
                    "channel_id": channel,
                    "user_input": f"Hello from {channel}",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
