# AI-Chat Orchestrator: Multi-Platform Chat Integration with AI

[![CircleCI](https://dl.circleci.com/status-badge/img/circleci/QJXxW5Kg3MhaRTXDr47FTf/bcb4e941-0b5f-479a-889b-9b98e69919c2/tree/dev.svg?style=shield)](https://dl.circleci.com/status-badge/redirect/circleci/QJXxW5Kg3MhaRTXDr47FTf/bcb4e941-0b5f-479a-889b-9b98e69919c2/tree/dev)
[![Coverage](https://img.shields.io/badge/coverage-80%2B%25-brightgreen)](https://app.circleci.com/pipelines/circleci/QJXxW5Kg3MhaRTXDr47FTf/bcb4e941-0b5f-479a-889b-9b98e69919c2)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Live Demo](https://img.shields.io/badge/demo-live%20on%20GCP-success)](https://ai-chat-orchestrator-qvzc7dnvtq-uc.a.run.app/docs)

This repository demonstrates a professional-grade microservices architecture for building AI-powered chat systems. The project emphasizes component-based design, dependency injection, and comprehensive testing to create a maintainable and extensible platform that integrates Discord, Slack, Jira, and Google Tasks with AI capabilities.

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

**Jira Integration:**
- `POST /jira/tickets` - Create Jira tickets
- `GET /jira/tickets` - List Jira tickets
- `GET /jira/tickets/{ticket_id}` - Get specific ticket

**Google Tasks Integration:**
- `POST /gtasks/tickets` - Create Google Tasks
- `GET /gtasks/tickets` - List Google Tasks
- `GET /gtasks/tickets/{task_id}` - Get specific task

**Health & Monitoring:**
- `GET /health` - Service health check


## Architectural Philosophy

This project is built on the principle of "programming integrated over time." The architecture is designed to combat complexity and ensure the system is maintainable and evolvable.

- **Component-Based Design**: The system is broken down into self-contained components. Each component has a single responsibility and can be reused across different projects with minimal effort.
- **Interface-Implementation Separation**: Every piece of functionality is defined by an abstract contract implemented as an ABC (the "what") and fulfilled by a concrete implementation (the "how"). This decouples business logic from specific technologies.
- **Dependency Injection**: Implementations are injected into abstract contracts at runtime. Consumers of the API only depend on stable interfaces, not volatile implementation details.

## Core Components

The project is a `uv` workspace containing multiple packages:

1. **`ai_client_api`**: Defines the abstract `AIClient` base class (ABC). This is the contract for AI operations.
2. **`gemini_client_impl`**: Provides the `GeminiClient` class, implementing AI capabilities using Google's Gemini API.
3. **`gemini_service`**: FastAPI service exposing Gemini AI capabilities via HTTP endpoints.
4. **`chat_client_api`**: Defines the abstract `ChatInterface` for chat platform operations.
5. **`discord_client_impl`**: Discord implementation of the chat interface.
6. **`slack_impl`**: Slack implementation of the chat interface.
7. **`ticket_api`**: Abstract ticket management interface.
8. **`jira_client_impl`**: Jira ticket system implementation.
9. **`gtask_client_impl`**: Google Tasks implementation.
10. **`ai_chat_orchestrator`**: Orchestration layer coordinating AI, chat, and ticket services.
11. **`orchestrator_service`**: FastAPI service providing unified HTTP API for all integrations.

## Project Setup

### 1. Prerequisites

- Python 3.11 or higher
- `uv` – A fast, all-in-one Python package manager
- Docker (optional, for deployment)
- GCP account (optional, for cloud deployment)

### 2. Initial Setup

1. **Install `uv`:**
    ```bash
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    ```

2. **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd hw1
    ```

3. **Set Up API Credentials:**
    - **Gemini API**: Obtain an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
    - **Jira** (Optional): Configure OAuth credentials for Jira integration
    - **Google Tasks** (Optional): Set up OAuth for Google Tasks integration
    - **Discord/Slack Tokens** (Optional): For chat platform integration

    Set environment variables:
    ```bash
    export GEMINI_API_KEY="your_gemini_api_key"
    export SLACK_BOT_TOKEN="your_slack_token"  # Optional
    export DISCORD_BOT_TOKEN="your_discord_token"  # Optional
    ```

    **Important:** Credential files contain secrets and are ignored by `.gitignore`.

4. **Create and Sync the Virtual Environment:**
    This single command creates a `.venv` folder and installs all packages defined in `uv.lock`.
    ```bash
    uv sync --all-packages --extra dev
    ```

5. **Activate the Virtual Environment:**
    ```bash
    # macOS / Linux
    source .venv/bin/activate
    # Windows (PowerShell)
    .venv\Scripts\Activate.ps1
    ```

6. **Run the Services:**
    ```bash
    # Start the orchestrator service
    uv run uvicorn orchestrator_service.api:app --port 8080 --reload

    # Access API documentation at http://localhost:8080/docs
    ```

## Development Workflow

All commands should be run from the project root with the virtual environment activated.

### Running the Application

To run the orchestrator service:
```bash
uv run uvicorn orchestrator_service.api:app --port 8080 --reload
```

### Running the Toolchain

- **Linting & Formatting (Ruff):**
    The project uses Ruff with comprehensive rules configured in `pyproject.toml`.
    ```bash
    # Check for issues
    uv run ruff check .
    # Automatically fix issues
    uv run ruff check . --fix
    # Check formatting
    uv run ruff format --check .
    # Apply formatting
    uv run ruff format .
    ```

- **Static Type Checking (MyPy):**
    ```bash
    uv run mypy src tests
    ```

- **Testing (Pytest):**

    I'd recommend running: `uv run pytest src/ tests/ -m "not local_credentials" -v` for simplicity.

    The project uses a comprehensive testing strategy with different test categories.
    ```bash
    # Run all tests (includes unit, integration, and e2e tests)
    uv run pytest

    # Run only unit tests (fast, no external dependencies - from src/ directories)
    uv run pytest src/

    # Run all tests except those requiring local credential files
    uv run pytest src/ tests/ -m "not local_credentials"

    # Run only integration tests (requires environment variables or credentials)
    uv run pytest -m integration

    # Run only end-to-end tests (requires credentials)
    uv run pytest -m e2e

    # Run tests with coverage reporting
    uv run pytest --cov=src --cov-report=term-missing
    ```

### Viewing Documentation

This project uses MkDocs for documentation.
```bash
# Start the live-reloading documentation server
uv run mkdocs serve
```
Open your browser to `http://127.0.0.1:8000` to view the site.

## Testing Infrastructure

The project implements a sophisticated testing strategy designed for both local development and CI/CD environments:

### Test Categories

- **Unit Tests** (`src/*/tests/`): Fast, isolated tests with mocked dependencies
- **Integration Tests** (`tests/integration/`): Tests that verify component interactions
- **End-to-End Tests** (`tests/e2e/`): Full application workflow tests with real services
- **CircleCI Tests**: CI/CD-compatible tests that handle missing credentials gracefully
- **Local Credentials Tests**: Tests that require OAuth credential files

### Test Markers

The project uses pytest markers to categorize tests:
```bash
@pytest.mark.unit              # Fast unit tests
@pytest.mark.integration       # Integration tests
@pytest.mark.e2e              # End-to-end tests
@pytest.mark.circleci         # CI/CD compatible
@pytest.mark.local_credentials # Requires local auth files
```

### Authentication in Tests

The testing infrastructure handles different authentication scenarios:
- **Local Development**: Uses credential files and environment variables
- **CI/CD Environment**: Uses CircleCI context variables
- **Missing Credentials**: Tests skip gracefully with clear messages (no hanging)

## Continuous Integration

The project includes a comprehensive CircleCI configuration (`.circleci/config.yml`) with multiple test stages:

- **All Branches**: Unit tests, linting, type checking, and CI-compatible tests
- **Main/Develop**: Additional integration and E2E tests with real API calls
- **Artifacts**: Coverage reports, test results, and build summaries

The CI pipeline automatically validates code quality and runs the full test suite on every push.

## Development Workflow Best Practices

### Quick Start
1. **Install dependencies**: `uv sync --all-packages --extra dev`
2. **Run tests**: `uv run pytest src/ tests/ -m "not local_credentials" -v`
3. **Check code quality**: `uv run ruff check . && uv run ruff format --check .`
4. **Fix formatting**: `uv run ruff format .`
5. **Type check**: `uv run mypy src tests`
6. **View documentation**: `uv run mkdocs serve`

### Development Tips
- Run unit tests (`uv run pytest src/`) during development for fast feedback
- Use integration tests (`uv run pytest -m integration`) to verify component interactions
- Run full test suite (`uv run pytest`) before pushing to ensure CI compatibility
- The CircleCI pipeline provides automated validation on every push

## Docker Deployment

### Build & Run Locally

```bash
# Build the orchestrator service
docker build --platform linux/amd64 -t orchestrator-service .

# Run locally
docker run -p 8080:8080 \
  -e GEMINI_API_KEY="your_api_key" \
  -e DISCORD_BOT_TOKEN="your_discord_token" \
  -e SLACK_BOT_TOKEN="your_slack_token" \
  orchestrator-service
```


