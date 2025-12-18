# Source Packages

This directory contains all the microservice packages that comprise the AI-Chat Orchestrator platform. Each package is independently tested, documented, and follows the component-based architecture pattern.

## Package Overview

### AI Client Layer

**[ai_client_api](ai_client_api/)** - Abstract base class defining the contract for AI service integrations.
- Provides `AIClient` ABC for standardized AI operations
- Supports both conversational and structured output modes
- Enables dependency injection and provider-agnostic design

**[gemini_client_impl](gemini_client_impl/)** - Google Gemini API implementation of the AIClient interface.
- Concrete implementation using Google's Gemini API
- Supports JSON schema-based structured output
- Registers with `ai_client_api` for dependency injection

**[gemini_service](gemini_service/)** - FastAPI service exposing Gemini AI capabilities via HTTP.
- REST API wrapper around `gemini_client_impl`
- Provides `/generate` endpoint for AI responses
- Health check and monitoring endpoints

**[gemini_adapter](gemini_adapter/)** - Adapter connecting AIClient interface to Gemini service via HTTP.
- Implements `AIClient` by delegating to remote Gemini service
- Enables microservices architecture with HTTP communication
- Uses auto-generated client from `gemini_ai_service_client`

**[gemini_ai_service_client](gemini_ai_service_client/)** - Auto-generated HTTP client for Gemini service.
- Type-safe Python bindings generated from OpenAPI spec
- Provides sync and async methods for all endpoints
- Do not manually edit - regenerate from service schema

### Chat Client Layer

**[chat_client_api](chat-client-api/)** - Abstract interface for chat platform operations.
- Defines `ChatInterface` ABC for channel and message management
- Standardizes operations across Discord, Slack, and other platforms
- Supports message retrieval, sending, and deletion

**[discord_client_impl](discord_client_impl/)** - Discord implementation of the chat interface.
- Integrates with Discord's Gateway API
- Provides channel and message management
- Includes Discord bot setup and event handling

**[slack_impl](slack_impl/)** - Slack implementation of the chat interface.
- Integrates with Slack Web API
- Supports channel operations and message posting
- Provides real Slack API client for production use

**[slack_adapter](slack_adapter/)** - Adapter for Slack API HTTP client.
- Wraps Slack HTTP operations
- Converts between interface contracts and Slack API
- Handles Slack-specific authentication

### Ticket Management Layer

**[ticket_api](ticket_api/)** - Abstract interface for ticket/task management systems.
- Defines `TicketInterface` for CRUD operations
- Provides `TicketStatus` enum (OPEN, IN_PROGRESS, CLOSED)
- Includes standardized adapters for different ticket systems

**[ticket_impl](ticket_impl/)** - Jira ticket system implementation.
- Concrete Jira integration using Jira REST API
- Supports OAuth 2.0 authentication
- Implements full ticket lifecycle management

**[jira_client_impl](jira_client_impl/)** - Jira-specific client implementation.
- Specialized Jira operations
- OAuth credential management
- Jira-specific field mapping

**[gtask_client_impl](gtask_client_impl/)** - Google Tasks implementation.
- Integrates with Google Tasks API
- OAuth 2.0 authentication
- Task creation and status management

**[tickets_client_impl](tickets_client_impl/)** - Legacy Google Tasks client.
- Alternative Google Tasks implementation
- Backward compatibility support
- Credential file-based authentication

**[task_client_service](task_client_service/)** - Service for task client operations.
- Additional task management utilities
- Dependency management for ticket clients
- Testing infrastructure

### Orchestration Layer

**[ai_chat_orchestrator](ai_chat_orchestrator/)** - Core orchestration logic coordinating AI, chat, and tickets.
- Coordinates message flow between chat platforms and AI services
- Maintains conversation history per channel
- Routes ticket commands to appropriate systems (Jira/Google Tasks)
- Tracks telemetry metrics (latency, success rates)
- Provides factory functions for Discord and Slack orchestrators

**[orchestrator_service](orchestrator_service/)** - FastAPI service providing unified HTTP API.
- Single REST API for all platform integrations
- Discord and Slack message processing endpoints
- Jira and Google Tasks ticket management endpoints
- Slack webhook handler with event deduplication
- Health checks and metrics endpoints
- Background task processing for long operations

## Architecture Patterns

### Dependency Injection

All packages follow the dependency injection pattern:

1. **Abstract Interface**: Define the contract (ABC)
2. **Concrete Implementation**: Implement the interface
3. **Registration**: Register implementation with API
4. **Factory**: Use factory to create instances

Example:
```python
# Define interface
from ai_client_api import AIClient

# Implement interface
import gemini_client_impl
gemini_client_impl.register()

# Use via factory
import ai_client_api
client = ai_client_api.get_client(api_key="key")
```

### Interface-Implementation Separation

Each domain has an API package (interface) and one or more implementation packages:

- `ai_client_api` → `gemini_client_impl`
- `chat_client_api` → `discord_client_impl`, `slack_impl`
- `ticket_api` → `ticket_impl`, `gtask_client_impl`

Business logic depends only on the interface, enabling easy swapping of implementations.

### Adapter Pattern

Adapters translate between different interfaces:

- `gemini_adapter`: Adapts HTTP client to `AIClient` interface
- `slack_adapter`: Adapts Slack HTTP client to `ChatInterface`
- `StandardizedTicketAdapter`: Adapts Jira client to common ticket interface
- `AsyncStandardizedTicketAdapter`: Adds async support to sync ticket clients

### Service Layer

Services expose internal functionality via HTTP:

- `gemini_service`: REST API for AI operations
- `orchestrator_service`: Unified API for all integrations

This enables microservices deployment and service-to-service communication.

## Package Dependencies

### Core Dependencies
```
ai_client_api → (no dependencies)
gemini_client_impl → ai_client_api, google-generativeai
chat_client_api → (no dependencies)
ticket_api → (no dependencies)
```

### Service Dependencies
```
gemini_service → ai_client_api, gemini_client_impl, fastapi
orchestrator_service → ai_chat_orchestrator, all client implementations, fastapi
```

### Orchestrator Dependencies
```
ai_chat_orchestrator → ai_client_api, chat_client_api, ticket_api
```

## Development Workflow

### Adding a New Package

1. Create package directory in `src/`
2. Add `pyproject.toml` with dependencies
3. Implement interface from corresponding API package
4. Write comprehensive tests
5. Create README.md documentation
6. Register in workspace `pyproject.toml`

### Testing Packages

```bash
# Test single package
pytest src/ai_client_api/tests/

# Test all packages
pytest src/

# Test with coverage
pytest src/ --cov=src --cov-report=term-missing
```

### Code Quality

All packages follow strict quality standards:

```bash
# Linting
uv run ruff check src/

# Formatting
uv run ruff format src/

# Type checking
uv run mypy src/
```

## Package Structure

Each package follows this structure:

```
package_name/
├── pyproject.toml          # Package metadata and dependencies
├── README.md               # Package documentation
├── src/
│   └── package_name/
│       ├── __init__.py     # Public API exports
│       ├── module.py       # Implementation files
│       └── tests/          # Unit tests
│           └── test_*.py
└── .python-version         # Python version
```

## Testing Strategy

### Unit Tests
- Located in each package's `tests/` directory
- Mock external dependencies
- Fast execution, no network calls
- Run in CI/CD pipeline

### Integration Tests
- Located in `tests/integration/`
- Test interactions between packages
- May require credentials
- Marked with `@pytest.mark.integration`

### End-to-End Tests
- Located in `tests/e2e/`
- Test full workflows across services
- Require all credentials
- Marked with `@pytest.mark.e2e`

## Deployment

### Local Development
```bash
uv sync --all-packages --extra dev
uv run uvicorn orchestrator_service.api:app --reload
```

### Docker
```bash
docker build -t orchestrator-service .
docker run -p 8080:8080 orchestrator-service
```

### Cloud (GCP Cloud Run)
```bash
gcloud run deploy orchestrator-service \
  --source . \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY=key
```

## Documentation

Each package includes:
- README.md with usage examples
- Docstrings on all public classes and methods
- Type hints for all function signatures
- Architecture and design principle documentation

API documentation is auto-generated using MkDocs:
```bash
uv run mkdocs serve
```

## Design Principles

### Component-Based Design
Each package is self-contained and reusable across projects.

### Interface Stability
Abstract interfaces remain stable; implementations can change freely.

### Dependency Direction
Dependencies flow from concrete implementations toward abstractions, never the reverse.

### Testing Isolation
Packages can be tested independently with mocked dependencies.

### Type Safety
All packages use comprehensive type hints validated by mypy.

### Minimal Coupling
Packages depend only on abstract interfaces, not concrete implementations.
