# Component Architecture

This project demonstrates a component-based architecture with clear separation between abstract contracts and concrete implementations. The system consists of multiple integrated layers that coordinate AI, chat platforms, and ticket management systems.

## Architecture Layers

### Layer 1: AI Client Integration

**ai_client_api** - Abstract AIClient interface
- `AIClient` ABC with `generate_response()` method
- Supports conversational and structured output (JSON schema)
- Factory pattern for client creation

**gemini_client_impl** - Google Gemini implementation
- Concrete implementation using Gemini API
- Supports text and JSON-structured responses
- Automatic registration pattern

**gemini_service** - FastAPI AI service
- REST API wrapper around Gemini client
- Health check and monitoring endpoints

**gemini_adapter** - HTTP adapter
- Implements AIClient by delegating to remote service
- Enables microservices architecture

### Layer 2: Chat Client Integration

**chat_client_api** - Abstract ChatInterface
- Channel and message management operations
- Standardized across Discord, Slack, and other platforms
- Methods: `get_channels()`, `send_message()`, `delete_message()`

**discord_client_impl** - Discord Gateway implementation
- Uses discord.py for bot functionality
- Event-driven message handling
- Real-time channel operations

**slack_impl** - Slack Web API implementation
- HTTP-based Slack client
- Channel operations and message posting
- Supports Slack-specific features

### Layer 3: Ticket Management Integration

**ticket_api** - Abstract ticket interface
- Adapter layer converting internal rich API to shared interface
- Priority handling via description prefix workaround
- Sync and async adapter implementations

**ticket_impl** - Jira REST API implementation
- OAuth 2.0 authentication with token storage
- User account ID lookup for reporter/assignee
- Full CRUD operations with priority support
- 30-60s latency due to OAuth and account lookups

**gtasks_client_impl** - Google Tasks implementation
- Google Tasks API integration
- String-based task IDs (vs Jira UUIDs)
- Fast response times (1-2 seconds)

**tickets_api** - Shared standardized interface
- Common `TicketStatus` enum (OPEN, IN_PROGRESS, CLOSED)
- Cross-system compatibility layer

### Layer 4: Orchestration Layer

**ai_chat_orchestrator** - Core coordination logic
- Message processing and AI integration
- Conversation history management (last 10 exchanges per channel)
- Ticket command routing (JIRA: and GTASKS: prefixes)
- Title-based updates with case-insensitive partial matching
- Priority extraction from description prefix with regex
- Polymorphic ID handling (UUID and string IDs)
- Telemetry tracking (latency, success rates)

**orchestrator_service** - Unified FastAPI service
- Discord and Slack message processing endpoints
- Jira and Google Tasks CRUD endpoints
- Slack webhook with background task processing
- Event deduplication cache (10-minute TTL)
- Health checks and metrics endpoints

## Component Structure

### Standard API Package Layout
```
src/<api_package>/
├── pyproject.toml           # Package configuration
├── README.md                # Component documentation
├── src/<api_package>/       # Source code
│   ├── __init__.py         # Public exports and factory functions
│   └── client.py           # ABC definitions
└── tests/                   # Unit tests
```

### Implementation Package Layout
```
src/<impl_package>/
├── pyproject.toml           # Package configuration
├── README.md                # Implementation documentation
├── src/<impl_package>/      # Source code
│   ├── __init__.py         # Registration and exports
│   └── client.py           # Concrete implementation
└── tests/                   # Unit tests with mocks
```

### Service Package Layout
```
src/<service_package>/
├── pyproject.toml           # Package configuration
├── README.md                # Service documentation
├── src/<service_package>/   # Source code
│   ├── api.py              # FastAPI router and endpoints
│   └── __init__.py         # Service initialization
└── tests/                   # API endpoint tests
```

### Orchestrator Package Layout
```
src/ai_chat_orchestrator/
├── pyproject.toml           # Package configuration
├── src/ai_chat_orchestrator/
│   ├── orchestrator.py     # Core orchestration logic
│   ├── __init__.py         # Factory functions
│   └── telemetry.py        # Metrics tracking
└── tests/                   # Unit and integration tests
```

## Dependency Injection Pattern

The project uses a factory-based dependency injection pattern:

1. **Abstract contracts** define factory functions that raise `NotImplementedError`
2. **Implementations** provide concrete factory functions
3. **Registration** happens at import time by rebinding the contract's factory:
   ```python
   ai_client_api.get_client = get_client_impl
   ```

This allows switching implementations without changing client code.

### Example: AI Client Registration

```python
# In ai_client_api/__init__.py
def get_client(api_key: str) -> AIClient:
    raise NotImplementedError("No AI client registered")

# In gemini_client_impl/__init__.py
from ai_client_api import AIClient

def get_client_impl(api_key: str) -> AIClient:
    return GeminiClient(api_key=api_key)

def register() -> None:
    ai_client_api.get_client = get_client_impl

register()  # Automatic registration on import

# Application code
import ai_client_api
import gemini_client_impl  # Triggers registration

client = ai_client_api.get_client("key")  # Returns GeminiClient
```

## Testing Strategy

### Component-Level Tests (Unit Tests)
- Located in each component's `tests/` directory (`src/*/tests/`)
- Test the public interface using mocks
- Isolate external dependencies
- Focus on the component's contract compliance
- Fast execution (milliseconds)
- Marked with `@pytest.mark.unit`

### Integration Tests
- Located in `tests/integration/`
- Test interactions between components
- Verify dependency injection works correctly
- May use real services or require credentials
- Marked with `@pytest.mark.integration`
- Medium execution time (seconds)

### End-to-End Tests
- Located in `tests/e2e/`
- Test complete workflows with real services
- Require actual API credentials
- Validate real-world scenarios
- Marked with `@pytest.mark.e2e`
- Slower execution (seconds to minutes)

### CI/CD Testing
- **CircleCI compatible** - Tests that work without local credential files
- **Local credentials** - Tests requiring OAuth token files
- **Markers**: `@pytest.mark.circleci`, `@pytest.mark.local_credentials`
- **Coverage requirement** - Minimum 85% code coverage

### Test Execution
```bash
# Unit tests only (fast)
uv run pytest src/

# All except local credentials (CI-friendly)
uv run pytest src/ tests/ -m "not local_credentials" -v

# Integration tests
uv run pytest -m integration

# E2E tests
uv run pytest -m e2e

# With coverage
uv run pytest --cov=src --cov-report=term-missing
```

## System Architecture

### High-Level Component Flow
```
┌────────────────────────────────────────┐
│   Client Applications                  │
│   (Discord Bot, Slack Bot, HTTP)       │
└───────────┬────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────┐
│   Orchestrator Service (FastAPI)      │
│   - Discord/Slack endpoints           │
│   - Jira/GTasks endpoints             │
│   - Webhook handlers                  │
└───────────┬───────────────────────────┘
            │
            ▼
┌───────────────────────────────────────┐
│   AI Chat Orchestrator                │
│   - Conversation history              │
│   - Command routing                   │
│   - Title-based operations            │
│   - Priority extraction               │
└──┬──────────┬────────────┬───────────┘
   │          │            │
   ▼          ▼            ▼
┌─────┐   ┌────────┐   ┌────────────┐
│ AI  │   │ Chat   │   │ Ticket     │
│     │   │        │   │            │
│Gemini│  │Discord │   │ Jira       │
│     │   │Slack   │   │ GTasks     │
└─────┘   └────────┘   └────────────┘
```

### Ticket System Architecture
```
┌──────────────────────────────────┐
│   tickets_api (Shared Interface) │
│   - Common TicketStatus enum     │
│   - Standardized operations      │
└────────────┬─────────────────────┘
             │
      ┌──────┴──────┐
      │             │
┌─────▼──────┐  ┌──▼──────────────┐
│ ticket_api │  │ gtasks_impl     │
│            │  │                 │
│ Adapter:   │  │ - Google Tasks  │
│ Internal → │  │ - String IDs    │
│ Shared     │  │ - Fast (1-2s)   │
│            │  │                 │
│ Priority:  │  └─────────────────┘
│ [PREFIX]   │
│            │
│ ticket_impl│
│ - Jira API │
│ - OAuth    │
│ - UUID IDs │
│ - Slow     │
│   (30-60s) │
└────────────┘
```

## Key Architectural Patterns

### 1. Adapter Pattern
- **ticket_api adapters** - Convert internal rich Jira API to shared interface
- **Priority workaround** - Prepends `[PRIORITY: VALUE]` to description field
- **Sync to Async** - AsyncStandardizedTicketAdapter wraps sync clients for FastAPI

### 2. Factory Pattern
- **Dependency injection** - Factory functions for creating clients
- **Registration pattern** - Implementations register at import time
- **Singleton orchestrators** - Global instances maintain conversation state

### 3. Orchestration Pattern
- **Central coordinator** - Orchestrator manages multi-service interactions
- **Command routing** - JIRA: and GTASKS: prefixes route to correct system
- **State management** - Conversation history per channel

### 4. Event-Driven Architecture
- **Slack webhooks** - Event-driven message processing
- **Background tasks** - Prevent timeout with async processing
- **Event deduplication** - Cache prevents duplicate processing

## Building New Components

To add a new component:

1. Create directory under `src/<component_name>/`
2. Add `pyproject.toml` with package metadata and dependencies
3. Implement the abstract interface or create a new one
4. Add to workspace members in root `pyproject.toml`
5. Write comprehensive unit tests with mocks
6. Document the component in its README
7. Register implementation if using dependency injection

This architecture ensures components are self-contained, testable, and easily replaceable.
