# HW2 - Gemini AI Service

## Overview

HW2 extends the project with a complete AI chat service built on Google's Gemini API. This follows the same component-based architecture as HW1 with clean separation between abstract contracts, implementations, and FastAPI service endpoints.

## Architecture Components

### 1. `gemini_api` - Abstract AI Client Interface

**Location:** `src/gemini_api/src/gemini_api/`

Defines the abstract contract for AI chat clients:

```python
class Message(ABC):
    """Abstract message in a conversation."""
    @property
    @abstractmethod
    def role(self) -> str: ...

    @property
    @abstractmethod
    def content(self) -> str: ...

class AIClient(ABC):
    """Abstract AI chat client interface."""
    @abstractmethod
    def send_message(self, user_id: str, message: str) -> str: ...

    @abstractmethod
    def get_conversation_history(self, user_id: str) -> list[Message]: ...

    @abstractmethod
    def clear_conversation(self, user_id: str) -> bool: ...
```

**Purpose:** Provides a provider-agnostic interface that any AI service (Gemini, OpenAI, etc.) can implement.

### 2. `gemini_impl` - Gemini Implementation

**Location:** `src/gemini_impl/src/gemini_impl/`

Concrete implementation using Google's Gemini 2.0 Flash model:

- **`GeminiClient`** - Implements `AIClient` interface with real Gemini API calls
  - Sends messages to Gemini and receives responses
  - Stores all conversation history in SQLite per user
  - Retrieves and clears conversation history

- **`MessageImpl`** - Concrete implementation of `Message` with role and content properties

- **`OAuthManager`** - Handles OAuth 2.0 authentication for Gmail integration
  - In-memory credential storage (session-scoped)
  - Token refresh handling
  - Credential revocation

**Features:**
- SQLite database for persistent conversation history (per-user databases)
- OAuth 2.0 support for Gmail integration
- Type-safe implementation with full mypy strict mode compliance

### 3. `gemini_service` - FastAPI Service

**Location:** `src/gemini_service/src/gemini_service/`

RESTful API wrapper around the Gemini client with user authentication and authorization:

#### Endpoints

**Chat Operations:**
- `POST /chat` - Send a message and get AI response
- `GET /history/{user_id}` - Retrieve conversation history
- `DELETE /history/{user_id}` - Clear conversation history

**OAuth Authentication:**
- `GET /auth/login` - Get OAuth authorization URL
- `GET /auth/callback` - Handle OAuth callback and exchange code for credentials
- `POST /auth/token` - Exchange authorization code for API key

#### Key Features

- **Per-User Clients** - Factory pattern creates separate clients per user with their own API keys
- **Authorization** - Users can only access their own resources
- **Flexible Client Type** - `AI_CLIENT_TYPE` environment variable controls which AI provider to use
- **OAuth Integration** - Base64-encoded or file-based Google credentials support
- **Mock Client Fallback** - When no API key is configured, service uses a mock client for testing

#### Dependency Injection

The service uses a factory-based dependency injection pattern:

```python
def _get_client_class() -> type[AIClient]:
    """Get the AI client class to instantiate (configurable via environment)."""
    client_type = os.getenv("AI_CLIENT_TYPE", "gemini")
    if client_type == "gemini":
        return GeminiClient
    raise ValueError(f"Unknown AI client type: {client_type}")

def _create_user_client(user_id: str, api_key: str) -> AIClient:
    """Create a client instance for a specific user."""
    client_class = _get_client_class()
    db_path = f"{data_dir}/conversations_{user_id}.db"
    return client_class(api_key=api_key, db_path=db_path)
```

This allows swapping implementations via environment configuration without modifying endpoint code.

### 4. `gemini_service_api_client` - Auto-Generated HTTP Client

**Location:** `src/gemini_service_api_client/`

Auto-generated from OpenAPI spec using `openapi-python-client`. Excluded from type checking due to auto-generation, but provides type hints for service clients.

### 5. `gemini_adapter` - HTTP Adapter

**Location:** `src/gemini_adapter/src/gemini_adapter/`

Adapter implementing the `AIClient` interface by making HTTP calls to the Gemini FastAPI service:

```python
class GeminiServiceAdapter(AIClient):
    """Adapter connecting abstract API to Gemini FastAPI service via HTTP."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.client = GeminiHTTPClient(base_url=base_url)

    def send_message(self, user_id: str, message: str) -> str:
        response = self.client.send_message_chat_post(
            json_body={"user_id": user_id, "message": message}
        )
        return response.response
```

**Purpose:** Allows other applications to use the Gemini service as a dependency without direct FastAPI coupling.

## Data Storage

### Conversation History - SQLite

- **Location:** Per-user database files (e.g., `conversations_user123.db`)
- **Schema:** Simple table with user_id, role, content, and timestamp
- **Persistence:** Survives service restarts
- **Multi-Instance:** Each instance has its own database file (suitable for single-instance HW2)

### API Keys - In-Memory Dictionary

- **Storage:** `_user_api_keys: dict[str, str]` in service memory
- **Scope:** Session-based (cleared on service restart)
- **Security:** Not persisted to disk
- **Purpose:** Tracks which users have provided API keys for authentication

### OAuth Credentials - In-Memory Dictionary

- **Storage:** `OAuthManager._credentials_cache: dict[str, Any]`
- **Scope:** Session-based (cleared on service restart)
- **Purpose:** Stores user OAuth tokens for Gmail integration
- **Refresh:** Automatically refreshes expired tokens on access

## Configuration

### Environment Variables

```bash
# AI Service Configuration
AI_CLIENT_TYPE=gemini              # Which AI provider to use
GEMINI_API_KEY=...                # Google Gemini API key
GEMINI_DB_PATH=conversations.db   # Base path for conversation databases

# OAuth Configuration (choose one)
GOOGLE_CREDENTIALS_B64=...        # Base64-encoded OAuth credentials JSON (production)
GOOGLE_CREDENTIALS_FILE=...       # Path to OAuth credentials JSON (development)
```

### Fly.io Deployment

For production on Fly.io, use base64-encoded credentials:

```bash
GOOGLE_CREDENTIALS_B64=$(cat credentials.json | base64)
```

The service automatically decodes and uses these credentials at startup.

## Testing Strategy

### Unit Tests
- Located in `src/gemini_*/tests/`
- Test individual components in isolation
- Use mocks and fixtures
- Run in CI/CD without credentials

### Integration Tests
- Test interactions between components
- Verify Gemini API integration
- Test OAuth flow (requires local credentials)
- Marked with `@pytest.mark.integration`

### E2E Tests
- Located in `tests/e2e/`
- Full system testing with real Gemini API
- Marked with `@pytest.mark.e2e` and `@pytest.mark.local_credentials`
- Requires valid GEMINI_API_KEY

### Running Tests

```bash
# Unit tests (CI-compatible)
uv run pytest src/ -m "circleci"

# With local credentials
uv run pytest src/ tests/ -m "not local_credentials"

# Full suite
uv run pytest src/ tests/
```

## Code Quality

### Type Checking (MyPy)
- `strict = true` configuration
- Cross-module type checking enabled
- Excluded modules:
  - Auto-generated clients (`*_service_api_client`)
  - External service modules that require credentials (`mail_client_service`)

### Linting (Ruff)
- `select = ["ALL"]` for comprehensive checking
- Justified ignores for:
  - Docstring style conflicts (D203, D213)
  - Assert usage in tests (S101)
  - Global statement for singleton pattern (PLW0603)

### Coverage
- Minimum 80% code coverage
- CircleCI CI/CD tracks coverage
- Local full suite achieves 85%+ coverage

## Deployment

### Local Development
```bash
uv run uvicorn gemini_service.main:app --reload
```

### Production (Fly.io)
```bash
# Uses combined app with both mail and gemini services
uv run python src/app.py
```

Deployed at: https://ospd-mail-client-hw1.fly.dev/docs

## Key Design Decisions

1. **Provider-Agnostic Interface** - Abstract `AIClient` allows swapping Gemini for other providers
2. **Per-User Clients** - Each user gets their own client instance with separate API key management
3. **SQLite Persistence** - Conversation history survives service restarts
4. **In-Memory Credentials** - Simpler for single-instance deployment; multi-instance would use shared DB
5. **Factory Pattern** - `_get_client_class()` and `_create_user_client()` provide flexibility without tight coupling
6. **OAuth for Gmail** - Future-proofs for Gmail integration while supporting direct API keys for Gemini

## Future Enhancements

- Shared credential storage for multi-instance deployments
- Conversation pagination and filtering
- Message search functionality
- Token-based rate limiting
- Conversation export (JSON, PDF)
- Multi-turn conversation context optimization
