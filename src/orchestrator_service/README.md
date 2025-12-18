# Orchestrator Service

FastAPI service providing unified HTTP API for AI-powered chat orchestration across Discord, Slack, Jira, and Google Tasks.

## Overview

The Orchestrator Service is the main HTTP API that brings together all components of the AI-Chat integration platform. It exposes REST endpoints for processing messages, managing channels, creating tickets, and retrieving metrics across multiple platforms.

## Architecture

The service follows a microservices-friendly architecture:

1. **API Layer**: FastAPI routes with request/response models
2. **Orchestration Layer**: Uses `ai_chat_orchestrator` to coordinate AI and chat operations
3. **Integration Layer**: Connects Discord, Slack, Jira, and Google Tasks implementations
4. **Singleton Pattern**: Maintains global orchestrator instances for efficiency

This design allows the service to be deployed as a standalone API or integrated into larger systems.

## API Endpoints

### Health Check

#### GET /health

Service health check for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "AI-Chat Orchestrator Service",
  "version": "1.0.0"
}
```

### Discord Integration

#### POST /discord/process

Process a Discord message with AI orchestration.

**Request:**
```json
{
  "channel_id": "channel-123",
  "user_input": "What are my open Jira tickets?"
}
```

**Response:**
```json
{
  "response": "Here are your 3 most recent tickets...",
  "success": true
}
```

#### GET /discord/channels

Get list of Discord channels.

**Response:**
```json
{
  "channels": [
    {"id": "channel-123", "name": "general"},
    {"id": "channel-456", "name": "dev-team"}
  ]
}
```

#### POST /discord/channels/{channel_id}/messages

Send a message to a Discord channel.

**Request:**
```json
{
  "content": "Hello from the API!"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": null
}
```

#### GET /discord/metrics

Get Discord orchestrator telemetry metrics.

**Response:**
```json
{
  "metrics": {
    "total_requests": 150,
    "successful_requests": 145,
    "failed_requests": 5,
    "success_rate": 0.97,
    "average_latency_seconds": 1.2
  }
}
```

### Slack Integration

#### POST /slack/process

Process a Slack message with AI orchestration.

**Request:**
```json
{
  "channel_id": "C123456",
  "user_input": "Summarize my Google Tasks"
}
```

**Response:**
```json
{
  "response": "You have 5 tasks...",
  "success": true
}
```

#### POST /webhook/slack

Slack Event API webhook endpoint.

**Features:**
- URL verification challenge handling
- Message event processing
- Event deduplication (10-minute TTL)
- Background task processing to prevent Slack retries
- Bot message filtering to prevent loops

**Request (URL Verification):**
```json
{
  "type": "url_verification",
  "challenge": "3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P"
}
```

**Response:**
```json
{
  "challenge": "3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P"
}
```

**Request (Message Event):**
```json
{
  "type": "event_callback",
  "event_id": "Ev123456",
  "event": {
    "type": "message",
    "channel": "C123456",
    "text": "Hello bot!",
    "user": "U123456"
  }
}
```

**Response:**
```json
{
  "ok": true
}
```

#### GET /slack/channels

Get list of Slack channels.

#### POST /slack/channels/{channel_id}/messages

Send a message to a Slack channel.

#### GET /slack/metrics

Get Slack orchestrator telemetry metrics.

### Jira Integration

#### POST /jira/tickets

Create a new Jira ticket.

**Request:**
```json
{
  "title": "Fix login bug",
  "description": "Users cannot log in with SSO",
  "assignee": "user@example.com"
}
```

**Response:**
```json
{
  "id": "12345678-1234-5678-1234-567812345678",
  "title": "Fix login bug",
  "description": "Users cannot log in with SSO",
  "status": "open",
  "assignee": "user@example.com"
}
```

#### GET /jira/tickets/{ticket_id}

Get a specific Jira ticket by ID.

**Response:**
```json
{
  "id": "12345678-1234-5678-1234-567812345678",
  "title": "Fix login bug",
  "description": "Users cannot log in with SSO",
  "status": "in_progress",
  "assignee": "user@example.com"
}
```

#### GET /jira/tickets

Search Jira tickets with optional filters.

**Query Parameters:**
- `query`: Search query string
- `status`: Filter by status (open, in_progress, closed)

**Response:**
```json
{
  "tickets": [
    {
      "id": "12345678-1234-5678-1234-567812345678",
      "title": "Fix login bug",
      "description": "Users cannot log in with SSO",
      "status": "open",
      "assignee": "user@example.com"
    }
  ]
}
```

### Google Tasks Integration

#### POST /gtasks/tickets

Create a new Google Tasks ticket.

**Request:**
```json
{
  "title": "Review pull request",
  "description": "Review PR #123 for new feature"
}
```

**Response:**
```json
{
  "id": "task-123",
  "title": "Review pull request",
  "description": "Review PR #123 for new feature",
  "status": "open",
  "assignee": null
}
```

#### GET /gtasks/tickets/{ticket_id}

Get a specific Google Tasks ticket by ID.

#### GET /gtasks/tickets

Search Google Tasks tickets with optional filters.

**Query Parameters:**
- `query`: Search query string
- `status`: Filter by status (open, in_progress, closed)

## Running the Service

### Local Development

```bash
# Install dependencies
uv sync --all-packages --extra dev

# Set environment variables
export GEMINI_API_KEY="your-gemini-api-key"
export SLACK_BOT_TOKEN="xoxb-your-slack-token"
export DISCORD_BOT_TOKEN="your-discord-token"
export JIRA_USER_ID="default_user"
export JIRA_PROJECT_KEY="PROJ"

# Run the service
uv run uvicorn orchestrator_service.api:app --port 8080 --reload
```

The service will be available at `http://localhost:8080`.

### API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`

### Docker Deployment

```bash
# Build the image
docker build -t orchestrator-service .

# Run the container
docker run -p 8080:8080 \
  -e GEMINI_API_KEY="your-api-key" \
  -e SLACK_BOT_TOKEN="your-slack-token" \
  -e DISCORD_BOT_TOKEN="your-discord-token" \
  orchestrator-service
```

### Cloud Deployment (GCP Cloud Run)

```bash
# Build for Cloud Run
docker build --platform linux/amd64 -t gcr.io/PROJECT_ID/orchestrator-service .

# Push to Google Container Registry
docker push gcr.io/PROJECT_ID/orchestrator-service

# Deploy to Cloud Run
gcloud run deploy orchestrator-service \
  --image gcr.io/PROJECT_ID/orchestrator-service \
  --platform managed \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY=your-key
```

## Configuration

### Environment Variables

**Required:**
- `GEMINI_API_KEY`: Google Gemini API key

**Optional:**
- `SLACK_BOT_TOKEN`: Slack Bot User OAuth Token (xoxb-)
- `SLACK_BASE_URL`: Slack API base URL (default: https://slack.com/api)
- `DISCORD_BOT_TOKEN`: Discord bot token
- `JIRA_USER_ID`: Jira user ID (default: default_user)
- `JIRA_PROJECT_KEY`: Jira project key (default: PROJ)

### Credential Files

The service supports credential files for Jira and Google Tasks OAuth:
- Jira: `credentials.json` with OAuth credentials
- Google Tasks: `token.json` with OAuth tokens

Place these in the project root or configure paths via environment.

## Features

### Multi-Platform Support

The service simultaneously supports:
- **Discord**: Gateway bot integration
- **Slack**: Event API and Web API
- **Jira**: Ticket creation and management
- **Google Tasks**: Task creation and management

### Intelligent Orchestration

- Maintains conversation history per channel
- Routes ticket commands to appropriate system (JIRA: or GTASKS:)
- Formats responses for Slack/Discord rendering
- Provides natural language summaries

### Event Handling

- **Slack Webhook**: Deduplicates events, processes in background
- **Discord Gateway**: Processes events via discord.py (not REST API)
- **Background Tasks**: Prevents timeout issues with chat platforms

### Telemetry

Tracks metrics per platform:
- Total requests
- Success/failure rates
- Average latency
- AI generation time
- Chat send time

## Architecture Details

### Singleton Orchestrators

The service maintains singleton instances:
- `_discord_orchestrator`: Discord AI orchestrator
- `_slack_orchestrator`: Slack AI orchestrator
- `_jira_ticket_client`: Sync Jira client (for orchestrator)
- `_jira_async_ticket_client`: Async Jira client (for FastAPI endpoints)
- `_gtasks_ticket_client`: Google Tasks client

This pattern ensures:
- Efficient resource usage
- Conversation history persistence
- Shared credential management

### NoOpChatClient

Discord uses a special `NoOpChatClient` because:
- Discord Gateway bot sends messages via discord.py
- REST API is not used for message sending
- Orchestrator still needs a chat client interface

### Async Adapters

Jira endpoints use `AsyncStandardizedTicketAdapter`:
- Wraps sync Jira client for FastAPI async compatibility
- Runs blocking operations in thread pool
- Maintains consistent async/await patterns

## Error Handling

The service provides detailed error responses:

- **400 Bad Request**: Invalid input parameters
- **404 Not Found**: Ticket not found
- **500 Internal Server Error**: Service errors with detailed messages

All errors are logged with context for debugging.

## Dependencies

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `ai_chat_orchestrator`: Orchestration logic
- `gemini_client_impl`: Gemini AI implementation
- `discord_client_impl`: Discord integration
- `slack_impl`: Slack API client
- `ticket_impl`: Jira implementation
- `tickets_client_impl`: Google Tasks implementation
- `pydantic`: Request/response validation

## Testing

Run tests with pytest:

```bash
pytest src/orchestrator_service/tests/
```

The test suite includes:
- Unit tests with mocked dependencies
- API endpoint tests using TestClient
- Validation tests for all request models
- Error handling tests

## Integration Examples

### Using with curl

```bash
# Process a message
curl -X POST http://localhost:8080/discord/process \
  -H "Content-Type: application/json" \
  -d '{"channel_id": "123", "user_input": "Hello"}'

# Create a Jira ticket
curl -X POST http://localhost:8080/jira/tickets \
  -H "Content-Type: application/json" \
  -d '{"title": "Bug", "description": "Fix issue"}'
```

### Using with Python

```python
import httpx

# Process message
response = httpx.post(
    "http://localhost:8080/slack/process",
    json={"channel_id": "C123", "user_input": "What are my tasks?"}
)
print(response.json())

# Get metrics
metrics = httpx.get("http://localhost:8080/slack/metrics")
print(metrics.json())
```

## Design Principles

### Unified API

Single service provides access to all platforms, reducing client complexity.

### Graceful Degradation

Services continue operating if optional integrations (Jira, Google Tasks) are unavailable.

### Event Deduplication

Slack webhook uses event cache to prevent duplicate processing from retries.

### Background Processing

Long-running operations use FastAPI BackgroundTasks to prevent timeouts.
