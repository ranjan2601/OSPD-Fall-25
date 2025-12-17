# AI-Chat Orchestrator: Multi-Platform Chat Integration with AI

[![CircleCI](https://dl.circleci.com/status-badge/img/circleci/QJXxW5Kg3MhaRTXDr47FTf/bcb4e941-0b5f-479a-889b-9b98e69919c2/tree/dev.svg?style=shield)](https://dl.circleci.com/status-badge/redirect/circleci/QJXxW5Kg3MhaRTXDr47FTf/bcb4e941-0b5f-479a-889b-9b98e69919c2/tree/dev)
[![Coverage](https://img.shields.io/badge/coverage-91%2B%25-brightgreen)](https://app.circleci.com/pipelines/circleci/QJXxW5Kg3MhaRTXDr47FTf/bcb4e941-0b5f-479a-889b-9b98e69919c2)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Live Demo](https://img.shields.io/badge/demo-live%20on%20GCP-success)](https://ai-chat-orchestrator-qvzc7dnvtq-uc.a.run.app/docs)

A professional-grade microservices architecture that orchestrates AI-powered chat across multiple platforms (Discord, Slack) with swappable providers and comprehensive telemetry.

## Live Demo

**Deployed Service**: https://ai-chat-orchestrator-qvzc7dnvtq-uc.a.run.app

**API Documentation**: https://ai-chat-orchestrator-qvzc7dnvtq-uc.a.run.app/docs

### Available Endpoints

**Discord Integration:**
- `POST /discord/process` - Process Discord messages with AI
- `GET /discord/channels` - List Discord channels
- `POST /discord/channels/{channel_id}/messages` - Send messages to Discord
- `GET /discord/metrics` - Get Discord orchestrator telemetry

**Slack Integration:**
- `POST /slack/process` - Process Slack messages with AI
- `GET /slack/channels` - List Slack channels
- `POST /slack/channels/{channel_id}/messages` - Send messages to Slack
- `GET /slack/metrics` - Get Slack orchestrator telemetry

**Health & Monitoring:**
- `GET /health` - Service health check


## Key Features

### 1. Provider Swapping
Switch between Discord and Slack without changing application code:
```python
# Both use the same ChatInterface
discord_orch = create_gemini_discord_orchestrator(gemini_api_key)
slack_orch = create_gemini_slack_orchestrator(gemini_api_key, slack_token)

# Same interface, different providers
discord_orch.process_direct(channel_id, "Hello!")
slack_orch.process_direct(channel_id, "Hello!")
```

### 2. Telemetry & Monitoring
Built-in metrics collection:
- **Request Latency**: AI generation time, chat send time, total latency
- **Success/Failure Rates**: Real-time success rate tracking
- **GCP Monitoring Dashboard**: Visualization of all metrics

### 3. Structured Output Support
AI can return both conversational and structured responses:
```python
# Conversational mode
response = ai_client.generate_response(
    user_input="What's the weather?",
    system_prompt="You are a helpful assistant"
)

# Structured output mode
response = ai_client.generate_response(
    user_input="List 3 colors",
    system_prompt="You are a helpful assistant",
    response_schema={"type": "array", "items": {"type": "string"}}
)
```

## Project Structure

```
ai-chat-orchestrator/
├── src/
│   ├── ai_client_api/              # Abstract AI client interface
│   ├── gemini_client_impl/         # Gemini AI implementation
│   ├── gemini_service/             # FastAPI Gemini HTTP service
│   ├── chat_client_api/            # Abstract chat client interface
│   ├── discord_client_impl/        # Discord implementation
│   ├── slack_impl/                 # Slack implementation
│   ├── ai_chat_orchestrator/       # Orchestration layer
│   └── orchestrator_service/       # FastAPI orchestrator HTTP service
├── terraform/                      # Infrastructure as Code
│   ├── main.tf                     # GCP Cloud Run, Secrets, Monitoring
│   ├── variables.tf                # Terraform variables
│   └── outputs.tf                  # Service URLs, dashboard links
├── tests/
│   ├── integration/                # Provider swapping tests
│   └── e2e/                        # End-to-end tests
├── docs/                           # MkDocs documentation
├── .circleci/                      # CI/CD configuration
├── Dockerfile                      # Production Docker build with health checks
└── DEPLOYMENT.md                   # GCP deployment guide
```

## Quick Start

### Prerequisites
- Python 3.11+
- `uv` package manager
- Docker (for deployment)
- GCP account (for cloud deployment)

### Local Development

```bash
# 1. Install dependencies
uv sync --all-packages --extra dev

# 2. Set environment variables
export GEMINI_API_KEY="your_gemini_api_key"
export SLACK_BOT_TOKEN="your_slack_token"  # Optional

# 3. Run the orchestrator service locally
uv run uvicorn orchestrator_service.main:app --reload

# 4. Access API docs at http://localhost:8000/docs
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run provider swapping tests
uv run pytest tests/integration/test_provider_swapping.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing
```

### View Documentation

```bash
# Start MkDocs server
uv run mkdocs serve

# Open http://localhost:8001
```

## Docker Deployment

### Build & Run Locally

```bash
# Build the orchestrator service
docker build --platform linux/amd64 -t orchestrator-service .

# Run locally
docker run -p 8000:8000 \
  -e GEMINI_API_KEY="your_api_key" \
  -e DISCORD_BOT_TOKEN="your_discord_token" \
  -e SLACK_BOT_TOKEN="your_slack_token" \
  orchestrator-service
```

### Deploy to GCP Cloud Run

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Monitoring & Observability

### Telemetry Metrics

The orchestrator tracks:
- **Total Requests**: Count of all processed messages
- **Success Rate**: Percentage of successfully processed messages
- **Failure Rate**: Percentage of failed messages
- **Average Latency**: Mean time to process messages
- **AI Generation Time**: Time spent calling AI service
- **Chat Send Time**: Time spent sending to chat platforms

### GCP Monitoring Dashboard

Access the dashboard:
```bash
# Get dashboard URL from Terraform output
cd terraform
terraform output dashboard_url
```

Dashboard visualizes:
- Request latency over time
- Success vs failure rate trends
- Per-service metrics (Discord/Slack)

## Testing Strategy

### Test Categories

1. **Unit Tests** (`src/*/tests/`): Fast, isolated tests
2. **Integration Tests** (`tests/integration/`): Provider swapping validation
3. **E2E Tests** (`tests/e2e/`): Full workflow tests
4. **CircleCI Tests**: CI/CD compatible

### Key Test: Provider Swapping

```python
def test_same_ai_different_chat_providers():
    """Verify Gemini AI works with both Discord and Slack."""
    discord_orch = create_gemini_discord_orchestrator(api_key)
    slack_orch = create_gemini_slack_orchestrator(api_key, slack_token)

    # Same AI, different platforms - should work identically
    assert discord_orch.ai_client == slack_orch.ai_client
```

## Documentation

Full documentation available at:
- **Live**: https://ai-chat-orchestrator-qvzc7dnvtq-uc.a.run.app/docs
- **Local**: `uv run mkdocs serve` → http://localhost:8001

### Documentation Sections

- **Overview**: Architecture and design principles
- **API Reference**: Auto-generated from code docstrings
  - AI Client API
  - Gemini Implementation
  - Chat Client API
  - Discord/Slack Implementations
  - Orchestrator API
- **Testing Guide**: Testing strategy and examples
- **HW3 - AI Chat Orchestrator**: Assignment-specific documentation

## Development

### Code Quality Tools

```bash
# Linting & formatting
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy src tests

# Tests
uv run pytest -v
```

### Adding a New Chat Provider

1. Implement `ChatInterface` in `src/new_provider_impl/`
2. Add factory function in `ai_chat_orchestrator/factory.py`
3. Add endpoints in `orchestrator_service/api.py`
4. Write integration tests
5. Update documentation

## Security & Credentials

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional (for Slack)
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_BASE_URL=https://slack.com/api
```

### GCP Secrets Manager

Credentials stored in Secret Manager:
- `gemini-api-key`: Gemini API key
- `slack-bot-token`: Slack bot token
- `discord-client-id`: Discord OAuth client ID
- `discord-client-secret`: Discord OAuth secret

## Workspace Structure

This is a `uv` workspace with multiple Python packages:

```toml
[tool.uv.workspace]
members = [
  "src/ai_client_api",
  "src/gemini_client_impl",
  "src/chat_client_api",
  "src/discord_client_impl",
  "src/slack_impl",
  "src/ai_chat_orchestrator",
  "src/orchestrator_service",
  # ... more packages
]
```

Each package is independently testable and reusable.

## CI/CD Pipeline

CircleCI automatically:
1. Runs linting and type checking
2. Executes full test suite
3. Validates provider swapping
4. Publishes coverage reports

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

This project is for educational purposes as part of the OSPD course at NYU.

