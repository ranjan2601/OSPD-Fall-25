# Contributing Guide

This guide provides an overview of the AI-Chat Orchestrator project architecture, design patterns, and development workflows. It is intended to help new contributors understand the foundational design principles and practices that guide this codebase.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Repository Structure](#repository-structure)
3. [Testing Strategy](#testing-strategy)
4. [Development Tools](#development-tools)

## Architecture Overview

This project demonstrates a component-based architecture built around the principle of "programming integrated over time." The design combats complexity through strict separation of concerns, clear interface boundaries, and dependency injection patterns that enable flexibility and maintainability.

### Core Design Philosophy

The AI-Chat Orchestrator platform is built on three fundamental principles:

1. **Component-Based Design**: The system is broken down into self-contained components. Each component has a single responsibility and can be reused across different projects with minimal effort.

2. **Interface-Implementation Separation**: Every piece of functionality is defined by an abstract contract implemented as an ABC (the "what") and fulfilled by a concrete implementation (the "how"). This decouples business logic from specific technologies.

3. **Dependency Injection**: Implementations are injected into abstract contracts at runtime. Consumers of the API only depend on stable interfaces, not volatile implementation details.

### Component Layers

The repository is organized as a `uv` workspace containing multiple layers of components:

#### AI Client Layer

**ai_client_api**: Abstract base class defining the contract for AI service integrations.
- Defines `AIClient` ABC with `generate_response()` method
- Supports both conversational and structured output modes (JSON schema)
- Factory pattern for creating client instances

**gemini_client_impl**: Google Gemini API implementation of the AIClient interface.
- Concrete implementation using Google's Gemini API
- Supports text responses and JSON-structured output
- Implements registration pattern to inject itself into `ai_client_api`

**gemini_service**: FastAPI service exposing Gemini AI capabilities via HTTP.
- REST API wrapper around `gemini_client_impl`
- Provides `/generate` endpoint for AI responses
- Health check and monitoring endpoints

**gemini_adapter**: Adapter connecting AIClient interface to Gemini service via HTTP.
- Implements `AIClient` by delegating to remote Gemini service
- Enables microservices architecture
- Uses auto-generated client from `gemini_ai_service_client`

#### Chat Client Layer

**chat_client_api**: Abstract interface for chat platform operations.
- Defines `ChatInterface` ABC for channel and message management
- Standardizes operations across Discord, Slack, and other platforms
- Methods: `get_channels()`, `get_messages()`, `send_message()`, `delete_message()`

**discord_client_impl**: Discord implementation of the chat interface.
- Integrates with Discord's Gateway API
- Provides channel and message management
- Uses discord.py library for bot functionality

**slack_impl**: Slack implementation of the chat interface.
- Integrates with Slack Web API
- Supports channel operations and message posting
- Real Slack API client for production use

#### Ticket Management Layer

**ticket_api**: Abstract interface for ticket/task management systems.
- Defines `TicketInterface` for CRUD operations
- Provides `TicketStatus` enum (OPEN, IN_PROGRESS, CLOSED)
- Includes standardized adapters for different ticket systems

**ticket_impl**: Jira ticket system implementation.
- Concrete Jira integration using Jira REST API
- Supports OAuth 2.0 authentication
- Implements full ticket lifecycle management

**gtask_client_impl**: Google Tasks implementation.
- Integrates with Google Tasks API
- OAuth 2.0 authentication
- Task creation and status management

#### Orchestration Layer

**ai_chat_orchestrator**: Core orchestration logic coordinating AI, chat, and tickets.
- Coordinates message flow between chat platforms and AI services
- Maintains conversation history per channel (last 10 exchanges)
- Routes ticket commands to appropriate systems (JIRA: or GTASKS: prefixes)
- Tracks telemetry metrics (latency, success rates)
- Provides factory functions for Discord and Slack orchestrators

**orchestrator_service**: FastAPI service providing unified HTTP API.
- Single REST API for all platform integrations
- Discord and Slack message processing endpoints
- Jira and Google Tasks ticket management endpoints
- Slack webhook handler with event deduplication
- Health checks and metrics endpoints
- Background task processing for long operations

### Dependency Injection Pattern

The project uses dependency injection to enable loose coupling between abstractions and implementations.

#### How It Works

**Step 1: Abstract Factory Functions**

The API packages define factory functions that initially raise `NotImplementedError`:

```python
# In ai_client_api
def get_client(api_key: str) -> AIClient:
    raise NotImplementedError("No AI client implementation registered")
```

**Step 2: Implementation Registration**

Implementation packages provide concrete factories and register them:

```python
# In gemini_client_impl/client.py
def get_client_impl(api_key: str) -> AIClient:
    return GeminiClient(api_key=api_key)

def register() -> None:
    """Register Gemini client with ai_client_api."""
    ai_client_api.get_client = get_client_impl
```

**Step 3: Automatic Registration at Import**

The registration happens automatically when the implementation is imported:

```python
# In gemini_client_impl/__init__.py
from .client import register

register()  # Dependency injection happens at import time
```

**Step 4: Application Usage**

Application code uses only the abstract interface:

```python
import ai_client_api
import gemini_client_impl  # Triggers registration

# Now get_client returns GeminiClient, but app only knows AIClient
client = ai_client_api.get_client(api_key="key")
response = client.generate_response("Hello", "You are helpful")
```

### Interface Design

#### Design Principles

**Deep Interfaces**: Interfaces provide powerful functionality behind simple APIs. The `AIClient.generate_response()` method appears simple but hides complexity:
- API authentication and credential management
- HTTP calls to AI services
- Response parsing and validation
- Error handling for network failures
- Structured output conversion

**Abstract Base Classes**: The project uses Python's `abc.ABC` for interface definitions rather than Protocol classes because:
- Explicit contracts with `@abstractmethod` decorators
- Runtime validation (TypeError if abstract methods not implemented)
- IDE support and type checking
- Clear documentation of required interface
- Conscious opt-in through inheritance

**Type Safety**: All interfaces use comprehensive type hints:
- Parameter types specified for all methods
- Return types explicitly declared
- Generic types used where appropriate (`Iterator[Message]`)
- mypy strict mode validates all type annotations

**Stable Contracts**: Interfaces remain stable while implementations evolve. New features added via optional parameters maintain backward compatibility.

### Component Interactions

The components interact through a clear, layered architecture:

**Application Layer**: Top-level code (orchestrator service, main scripts) imports abstract APIs and implementation packages. Uses only abstract interfaces for all operations.

**Orchestration Layer**: `ai_chat_orchestrator` coordinates between AI, chat, and ticket clients. Depends only on abstract interfaces, enabling any combination of implementations.

**Service Layer**: FastAPI services expose functionality via HTTP endpoints. Enable microservices deployment and service-to-service communication.

**Adapter Layer**: Adapters translate between different interfaces. Examples: `AsyncStandardizedTicketAdapter` (sync to async), `SlackChatClient` (Slack API to ChatInterface).

**Implementation Layer**: Concrete implementations fulfill abstract contracts. Each depends on its corresponding API package and external libraries.

## Repository Structure

### Project Organization

The repository follows a strict directory structure that separates concerns:

```
hw1/
├── src/                        # All workspace member packages
│   ├── ai_client_api/         # AI client abstract interface
│   ├── gemini_client_impl/    # Gemini implementation
│   ├── gemini_service/        # Gemini FastAPI service
│   ├── gemini_adapter/        # HTTP adapter for Gemini service
│   ├── gemini_ai_service_client/  # Auto-generated HTTP client
│   ├── chat_client_api/       # Chat platform abstract interface
│   ├── discord_client_impl/   # Discord implementation
│   ├── slack_impl/            # Slack implementation
│   ├── ticket_api/            # Ticket system abstract interface
│   ├── ticket_impl/           # Jira implementation
│   ├── gtask_client_impl/     # Google Tasks implementation
│   ├── ai_chat_orchestrator/  # Orchestration logic
│   └── orchestrator_service/  # Orchestrator FastAPI service
├── tests/                      # Integration and E2E tests
│   ├── integration/           # Component interaction tests
│   └── e2e/                   # Full workflow tests
├── docs/                       # MkDocs documentation
├── terraform/                  # Infrastructure as code
├── .circleci/                 # CI/CD configuration
├── pyproject.toml             # Root workspace configuration
├── uv.lock                    # Locked dependencies
├── mkdocs.yml                 # Documentation config
└── README.md                  # Project overview
```

### Package Structure

Each component follows the "src layout" pattern:

```
component_name/
├── pyproject.toml          # Package metadata and dependencies
├── README.md               # Package documentation
└── src/
    └── component_name/
        ├── __init__.py     # Public API exports
        ├── module.py       # Implementation files
        └── tests/          # Unit tests
            └── test_*.py
```

### Configuration Files

#### Root `pyproject.toml`

The root configuration defines:
- **Workspace members**: All packages in the monorepo
- **Development dependencies**: pytest, ruff, mypy, mkdocs
- **Tool configuration**: Default settings for linting, formatting, type checking
- **Test configuration**: pytest markers, coverage thresholds
- **Build system**: How the workspace is built

#### Component `pyproject.toml`

Each component declares:
- **Component metadata**: Name, version, description
- **Runtime dependencies**: External libraries and workspace packages
- **Workspace sources**: Which dependencies come from the workspace
- **Build system**: How the component is packaged
- **Tool overrides**: Component-specific settings if needed

### Import Guidelines

The project uses **absolute imports** consistently:

```python
# Good: Absolute imports
from ai_client_api import AIClient
from gemini_client_impl.client import GeminiClient

# Bad: Relative imports
from . import client
from ..api import AIClient
```

**Import organization**:
1. Standard library imports
2. Third-party library imports
3. Local workspace imports

All imports sorted alphabetically within each group.

### Keeping `__init__.py` Slim

Package `__init__.py` files should:
- Import and re-export public API components
- Define `__all__` to control exports
- Perform registration (implementation packages only)
- Avoid business logic or complex operations

```python
# Good __init__.py
"""Public API for ai_client_api."""

from .client import AIClient, get_client

__all__ = ["AIClient", "get_client"]
```

Test directory `__init__.py` files should be completely empty.

## Testing Strategy

### Testing Philosophy

The project follows modern software engineering testing principles:

**Quality is Everyone's Responsibility**: All contributors write tests, review tests, and maintain test quality. Quality is integrated into daily development, not a separate phase.

**Quality is the Absence of Defects**: Tests prevent defects and provide confidence. The goal is meaningful tests, not high coverage percentages.

**Test Pyramid**: Majority unit tests (fast, reliable), fewer integration tests (verify interactions), minimal E2E tests (validate workflows).

**FIRST Principles**: All unit tests must be:
- **Fast**: Run in milliseconds, mock external dependencies
- **Isolated**: Independent, no shared state
- **Repeatable**: Deterministic results every time
- **Self-Verifying**: Clear pass/fail with assertions
- **Timely**: Written alongside production code

**Arrange-Act-Assert Pattern**: All tests follow AAA structure for clarity.

### Test Organization

#### Unit Tests

Located in each component's `tests/` directory: `src/*/tests/`

**Characteristics**:
- Fast execution (milliseconds)
- All external dependencies mocked
- Test individual classes/methods
- Marked with `@pytest.mark.unit`

**Example**:
```python
def test_generate_response_success():
    # Arrange
    client = MockAIClient()

    # Act
    response = client.generate_response("Hello", "Be helpful")

    # Assert
    assert response == "Expected response"
```

#### Integration Tests

Located in `tests/integration/`

**Characteristics**:
- Medium execution speed (seconds)
- Test component interactions
- May use real APIs with credentials
- Marked with `@pytest.mark.integration`

**What they test**:
- Dependency injection works correctly
- Components communicate properly
- Factory functions return correct implementations
- Authentication flows work end-to-end

#### End-to-End Tests

Located in `tests/e2e/`

**Characteristics**:
- Slowest execution (seconds to minutes)
- Test complete workflows
- Use real systems and APIs
- Marked with `@pytest.mark.e2e`

**What they test**:
- Complete user workflows
- Application entry points
- All components integrate in real scenarios

### Code Coverage

The project enforces **minimum 85% code coverage** using pytest-cov.

**Configuration** (in root `pyproject.toml`):
```toml
[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/main.py"]

[tool.coverage.report]
fail_under = 85
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

**Running tests with coverage**:
```bash
# All tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Unit tests only
uv run pytest src/ --cov=src --cov-report=term-missing

# Exclude tests requiring local credentials
uv run pytest src/ tests/ -m "not local_credentials" -v

# Generate HTML report
uv run pytest --cov=src --cov-report=html
```

### Test Categories and Markers

Tests are categorized using pytest markers:

```python
@pytest.mark.unit              # Fast unit tests
@pytest.mark.integration       # Integration tests
@pytest.mark.e2e              # End-to-end tests
@pytest.mark.circleci         # CI/CD compatible
@pytest.mark.local_credentials # Requires local credential files
```

**Running specific test categories**:
```bash
# Only unit tests
pytest -m unit

# Only integration tests
pytest -m integration

# All except local credentials (for CI)
pytest -m "not local_credentials"
```

## Development Tools

### Workspace Management (uv)

The project uses **uv** for fast Python package management.

**Initial setup**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install all dependencies
uv sync --all-packages --extra dev

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\Activate.ps1  # Windows
```

**Common commands**:
```bash
# Add dependency to a component
uv add --package component-name library-name

# Add dev dependency to workspace
uv add --dev pytest-plugin

# Update all dependencies
uv sync --upgrade

# Run command without activating venv
uv run pytest

# Show dependency tree
uv tree
```

### Static Analysis and Formatting

**Ruff** handles both linting and formatting:

```bash
# Check for linting issues
uv run ruff check .

# Auto-fix linting issues
uv run ruff check . --fix

# Check code formatting
uv run ruff format --check .

# Apply code formatting
uv run ruff format .
```

**MyPy** handles static type checking:

```bash
# Type check source and tests
uv run mypy src tests
```

**Pre-commit workflow**:
```bash
uv run ruff check . --fix
uv run ruff format .
uv run mypy src tests
uv run pytest
```

### Documentation Generation

**MkDocs** generates documentation from Markdown:

```bash
# Start development server with live reload
uv run mkdocs serve

# Build static HTML
uv run mkdocs build

# Output is in site/ directory
```

Documentation is configured in `mkdocs.yml` and source files are in `docs/`.

### Continuous Integration

The project uses **CircleCI** for CI/CD. The pipeline is defined in `.circleci/config.yml`.

**CI Jobs**:
1. **build**: Install dependencies and set up workspace
2. **lint**: Run ruff linting
3. **unit_test**: Run unit tests with coverage
4. **circleci_test**: Run all CI-compatible tests
5. **integration_test**: Run integration tests (main/develop only)
6. **report_summary**: Aggregate results

**Triggers**:
- Every `git push` to any branch
- Every commit to pull requests
- Manual re-run via CircleCI UI

**Branch-specific workflows**:
- **Feature branches**: build, lint, unit_test, circleci_test
- **Main/develop**: All jobs including integration_test

**Environment variables** (stored in CircleCI context):
- `GEMINI_API_KEY`: Google Gemini API key
- `SLACK_BOT_TOKEN`: Slack Bot OAuth token
- `DISCORD_BOT_TOKEN`: Discord bot token
- OAuth credentials for Jira and Google Tasks

### Development Workflow

**Setting up for development**:
```bash
# Clone and setup
git clone <repository-url>
cd hw1
uv sync --all-packages --extra dev
source .venv/bin/activate
```

**Making changes**:
```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes to code

# Run quality checks
uv run ruff format .
uv run ruff check .
uv run mypy src tests
uv run pytest

# Commit and push
git add .
git commit -m "Add feature"
git push origin feature/my-feature
```

**Running services locally**:
```bash
# Run orchestrator service
uv run uvicorn orchestrator_service.api:app --port 8080 --reload

# Access API docs at http://localhost:8080/docs
```

## Best Practices

### Code Quality

1. **Write tests first or alongside code**: Don't wait until the end
2. **Keep functions small**: Single responsibility principle
3. **Use type hints everywhere**: Enable static type checking
4. **Handle errors gracefully**: Use proper exception handling
5. **Document public APIs**: Clear docstrings for all public methods
6. **Follow SOLID principles**: Single responsibility, open/closed, dependency inversion

### Testing

1. **Test behaviors, not methods**: Focus on what the code does
2. **Test via public APIs**: Don't test private implementation details
3. **Use descriptive test names**: Clearly state what's being tested
4. **Keep tests simple**: No complex logic in test code
5. **Mock external dependencies**: Unit tests should be fast and isolated
6. **Write complete tests**: Everything needed to understand the test is in the test itself

### Git Workflow

1. **Use descriptive commit messages**: Explain what and why
2. **Keep commits focused**: One logical change per commit
3. **Write commit messages in imperative mood**: "Add feature" not "Added feature"
4. **Reference issues in commits**: Link to tracking system
5. **Review your own changes before pushing**: Catch mistakes early

## Getting Started

Ready to contribute? Follow these steps:

```bash
# 1. Clone and setup
git clone <repository-url>
cd hw1
uv sync --all-packages --extra dev
source .venv/bin/activate

# 2. Run tests to verify setup
uv run pytest src/ tests/ -m "not local_credentials" -v

# 3. Make changes and run checks
uv run ruff format .
uv run ruff check .
uv run mypy src tests
uv run pytest

# 4. View documentation
uv run mkdocs serve

# 5. Push changes
git push origin your-branch
```

For questions or issues, refer to the project README or open a GitHub issue.
