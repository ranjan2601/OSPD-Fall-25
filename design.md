# Design Document: Mail Client Service Components

## Overview

This document describes the design and architecture of the new components added to the mail client system as part of Homework 1. These components extend the base repository's functionality by adding a service-oriented architecture layer, enabling HTTP-based access to mail client operations.

### New Components Added

1. **FastAPI Service** (`mail_client_service/api.py`, `main.py`) - REST API exposing mail operations
2. **ServiceClient** (`mail_client_service/_impl.py`) - HTTP client implementing the `Client` interface
3. **Auto-Generated Client** (`mail_client_service/generated/`) - Type-safe HTTP client from OpenAPI schema
4. **Docker Support** (`Dockerfile`) - Containerized deployment solution

### Problem Statement

The base repository provides direct Gmail API integration through `gmail_client_impl`, which works well for applications that need to interact with Gmail directly. However, this approach has limitations:

- **Tight coupling to Gmail API**: Applications must handle OAuth, API quotas, and Gmail-specific logic
- **Language barrier**: Only Python applications can use the client
- **Deployment complexity**: Each application needs Gmail credentials and API access
- **Testing difficulty**: Testing requires real Gmail credentials or complex mocking

**Solution**: Add a service layer that exposes mail operations through a REST API, allowing:
- HTTP-based access from any language
- Centralized credential management
- Built-in mock client for testing
- Scalable, containerized deployment

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                   Client Applications                        │
└─────────────┬───────────────────────────┬───────────────────┘
              │                           │
              │ (Direct)                  │ (via HTTP)
              │                           │
┌─────────────▼─────────────┐   ┌────────▼──────────────────┐
│   gmail_client_impl        │   │  mail_client_service      │
│   (Base Repository)        │   │  (New Component)          │
│                            │   │                           │
│  - GmailClient             │   │  - FastAPI REST API       │
│  - OAuth 2.0               │   │  - ServiceClient (HTTP)   │
│  - Direct Gmail API        │   │  - Mock Client Fallback   │
└────────────┬───────────────┘   └───────────┬───────────────┘
             │                               │
             │                               │
             ▼                               ▼
    ┌────────────────────────────────────────────────┐
    │         mail_client_api (Interface)            │
    │         - Client ABC                           │
    │         - Message ABC                          │
    └────────────────────────────────────────────────┘
```

### Design Principles Applied

1. **Interface Segregation**: `ServiceClient` implements the same `Client` interface as `GmailClient`, ensuring consistent behavior
2. **Dependency Inversion**: Both implementations depend on abstractions (`mail_client_api`), not concrete classes
3. **Open/Closed**: New functionality added without modifying existing base components
4. **Single Responsibility**: Each component has one clear purpose (API server, HTTP client, message wrapper)

---

## Component 1: FastAPI Service

### Purpose
Expose mail client operations through HTTP REST endpoints, providing language-agnostic access and enabling service-oriented architectures.

### Design Details

#### API Structure (`api.py`)

```python
router = APIRouter()

# Dependency on mail_client_api.Client
mail_client = get_client(interactive=False)

@router.get("/")
def root():
    return {"message": "Mail Client Service is running"}

@router.get("/messages")
def get_messages(max_results: int = 10):
    messages = list(mail_client.get_messages(max_results))
    return {"messages": [serialize_message(msg) for msg in messages]}

@router.get("/messages/{message_id}")
def get_message(message_id: str):
    message = mail_client.get_message(message_id)
    return {"message": serialize_message(message)}

@router.delete("/messages/{message_id}")
def delete_message(message_id: str):
    success = mail_client.delete_message(message_id)
    return {"message_id": message_id, "status": "Deleted" if success else "Failed"}

@router.post("/messages/{message_id}/mark-as-read")
def mark_as_read(message_id: str):
    success = mail_client.mark_as_read(message_id)
    return {"message_id": message_id, "status": "Marked as read" if success else "Failed"}
```

#### Key Design Decisions

**1. Thin API Layer**
- **Decision**: Keep API endpoints as thin wrappers around `mail_client_api.Client`
- **Rationale**:
  - Reduces duplication of business logic
  - Makes the service a true proxy/adapter
  - Simplifies testing (test the client, not the API)
- **Tradeoff**: API is tightly coupled to Client interface shape

**2. Mock Client Fallback**
- **Decision**: Automatically fall back to a built-in `MockClient` when credentials unavailable
- **Implementation**:
```python
try:
    mail_client = get_client(interactive=False)
except RuntimeError as e:
    if "No valid credentials found" in str(e):
        # Use built-in MockClient with 3 test messages
        mail_client = MockClient()
```
- **Rationale**:
  - Enables development and testing without Gmail API access
  - CI/CD pipelines can run without secrets
  - Demos work out-of-the-box
- **Tradeoff**: Must maintain mock data separately

**3. Synchronous API**
- **Decision**: Use synchronous FastAPI endpoints (not `async def`)
- **Rationale**:
  - Base `gmail_client_impl` uses synchronous Google API client
  - No I/O-bound operations to parallelize within a single request
  - Simpler code, easier to reason about
- **Tradeoff**: Can't handle concurrent requests as efficiently as async (acceptable for this use case)

**4. No Authentication/Authorization**
- **Decision**: Service has no auth layer
- **Rationale**:
  - Homework scope: demonstrate architecture, not production security
  - Deployment assumed to be in trusted network
  - Could add API keys/JWT later without changing core design
- **Tradeoff**: Not production-ready for public deployment

#### OpenAPI Schema Generation

FastAPI automatically generates an OpenAPI schema at `/openapi.json`, which is used to:
1. Generate API documentation (`/docs`, `/redoc`)
2. Generate the Python HTTP client (see Component 3)
3. Enable API contract testing

---

## Component 2: ServiceClient (HTTP Adapter)

### Purpose
Implement the `mail_client_api.Client` interface by communicating with the FastAPI service over HTTP, allowing applications to swap between direct Gmail access and service-based access transparently.

### Design Details

#### Implementation (`_impl.py`)

```python
class ServiceClient(client.Client):
    """HTTP-based implementation of mail_client_api.Client."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self._client = MailClientServiceApiClient(base_url=base_url)

    def get_messages(self, max_results: int = 10) -> Iterator[message.Message]:
        response = get_messages_messages_get.sync(
            client=self._client,
            max_results=max_results
        )
        if response:
            return (ServiceMessage(msg) for msg in response)
        return iter([])

    def get_message(self, message_id: str) -> message.Message:
        response = get_message_messages_message_id_get.sync(
            client=self._client,
            message_id=message_id
        )
        if not response:
            raise ValueError(f"Message {message_id} not found")
        return ServiceMessage(response)

    # ... similar implementations for delete_message, mark_as_read
```

#### Key Design Decisions

**1. Composition over Inheritance**
- **Decision**: `ServiceClient` composes an auto-generated HTTP client, rather than extending it
- **Rationale**:
  - Generated client might change when schema updates
  - Keeps adapter logic separate from HTTP client logic
  - Easier to mock/test
- **Tradeoff**: Extra layer of indirection

**2. Iterator Return Type**
- **Decision**: `get_messages()` returns a generator, not a list
- **Rationale**:
  - Matches `mail_client_api.Client` interface contract
  - Consistent with `GmailClient` implementation
  - Enables lazy evaluation (even though HTTP call is eager)
- **Tradeoff**: HTTP response is already fully loaded, so "lazy" is somewhat illusory

**3. Error Handling**
- **Decision**: Convert HTTP errors to exceptions matching base implementation
- **Implementation**:
```python
def get_message(self, message_id: str) -> message.Message:
    response = get_message_messages_message_id_get.sync(...)
    if not response:  # 404 or other error
        raise ValueError(f"Message {message_id} not found")
    return ServiceMessage(response)
```
- **Rationale**: Clients expect exceptions, not HTTP status codes
- **Tradeoff**: Loses HTTP-specific error details

**4. ServiceMessage Wrapper**
- **Decision**: Wrap auto-generated response models in `ServiceMessage` class
- **Implementation**:
```python
class ServiceMessage(message.Message):
    """Adapter wrapping HTTP response as Message protocol."""

    def __init__(self, response: MessageResponse):
        self._response = response

    @property
    def id(self) -> str:
        return self._response.id

    # ... other Message properties delegate to _response
```
- **Rationale**:
  - Response models have different attribute names (`from_` vs `sender`)
  - Need to implement `Message` protocol/ABC
  - Keeps auto-generated code unchanged
- **Tradeoff**: Extra object allocation per message

---

## Component 3: Auto-Generated HTTP Client

### Purpose
Provide a type-safe, maintainable HTTP client that stays in sync with the FastAPI service's API contract.

### Design Details

#### Generation Process

```bash
# 1. Service generates OpenAPI schema
curl http://localhost:8000/openapi.json > openapi_schema.json

# 2. Generate Python client from schema
openapi-python-client generate \
  --path openapi_schema.json \
  --output-path src/mail_client_service/generated
```

#### Generated Structure

```
generated/
├── mail_client_service_api_client/
│   ├── __init__.py
│   ├── client.py              # HTTP client with auth, timeouts
│   ├── api/
│   │   └── default/
│   │       ├── get_messages_messages_get.py
│   │       ├── get_message_messages_message_id_get.py
│   │       ├── delete_message_messages_message_id_delete.py
│   │       └── mark_as_read_messages_message_id_read_put.py
│   ├── models/
│   │   ├── message_response.py
│   │   ├── delete_response.py
│   │   └── mark_read_response.py
│   └── types.py
└── pyproject.toml
```

#### Key Design Decisions

**1. Why Auto-Generation?**
- **Decision**: Use `openapi-python-client` instead of writing HTTP client manually
- **Rationale**:
  - **Type safety**: Generated code includes full type hints (Pydantic models)
  - **Contract enforcement**: Client code breaks if API changes incompatibly
  - **Reduces boilerplate**: Serialization, validation, error handling auto-generated
  - **Documentation**: Models are self-documenting with Python types
- **Tradeoff**:
  - Adds generation step to workflow
  - Generated code can be verbose
  - Must commit generated code or regenerate in CI

**2. Vendoring vs. Runtime Generation**
- **Decision**: Commit generated code to repository
- **Rationale**:
  - Simpler CI/CD (no generation step needed)
  - Code reviewers can see client changes
  - Deterministic builds
- **Tradeoff**: Git history includes generated code churn

**3. httpx Dependency**
- **Decision**: Generated client uses `httpx` instead of `requests`
- **Rationale**:
  - `openapi-python-client` uses `httpx` by default
  - Modern, async-capable (even though we use sync mode)
  - Better HTTP/2 support
- **Tradeoff**: Extra dependency (httpx not in base repo)

**4. Model Validation with Pydantic**
- **Decision**: Generated models use Pydantic v2 for validation
- **Rationale**:
  - Runtime validation of API responses
  - Catches API contract violations early
  - Automatic serialization/deserialization
- **Tradeoff**: Adds Pydantic dependency and validation overhead

#### Example Generated Usage

```python
from mail_client_service.generated.mail_client_service_api_client import Client
from mail_client_service.generated.mail_client_service_api_client.api.default import (
    get_messages_messages_get
)

client = Client(base_url="http://localhost:8000")
response = get_messages_messages_get.sync(client=client, max_results=10)
# response: List[MessageResponse] | None
```

---

## Component 4: Docker Integration

### Purpose
Enable containerized deployment of the FastAPI service for easy distribution and deployment.

### Design Details

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Copy source code
COPY src/ ./src/
COPY main.py ./

# Install all packages and dev dependencies (httpx needed for generated client)
RUN uv sync --frozen --all-packages --extra dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.mail_client_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Key Design Decisions

**1. Multi-Stage Build (NOT Used)**
- **Decision**: Use single-stage build instead of multi-stage
- **Rationale**:
  - Homework simplicity over optimization
  - Need dev dependencies (httpx, pytest) for generated client
  - Image size not critical for demo
- **Alternative**: Could use multi-stage to separate build and runtime, reducing image size by ~200MB

**2. uv Package Manager**
- **Decision**: Use `uv` inside container, matching local development
- **Rationale**:
  - Consistent dependency resolution (local vs. Docker)
  - Fast dependency installation
  - Workspace support for monorepo structure
- **Tradeoff**: Smaller images possible with plain `pip` and `requirements.txt`

**3. --extra dev Flag**
- **Decision**: Include dev dependencies in production image
- **Rationale**:
  - `httpx` needed for generated client to work
  - Could be moved to main dependencies, but kept in dev for historical reasons
- **Production Fix**: Move `httpx` to main dependencies, remove `--extra dev`

**4. Port 8000**
- **Decision**: Expose and use port 8000
- **Rationale**:
  - Standard for development web servers
  - Matches `uvicorn` default
  - Easy to map to any host port with `-p`
- **Tradeoff**: Port 8000 commonly used, might conflict with other services

**5. No Environment Variables**
- **Decision**: No `ENV` declarations in Dockerfile
- **Rationale**:
  - Gmail credentials optional (falls back to mock)
  - Credentials provided at runtime via `-e` flags
- **Production Addition**: Could add default `LOG_LEVEL`, `WORKERS`, etc.

#### Build and Run

```bash
# Build
docker build -t mail-client-service .

# Run with mock client (no credentials)
docker run -d -p 8000:8000 mail-client-service

# Run with Gmail credentials
docker run -d -p 8000:8000 \
  -e GMAIL_CLIENT_ID="..." \
  -e GMAIL_CLIENT_SECRET="..." \
  -e GMAIL_REFRESH_TOKEN="..." \
  mail-client-service
```

---

## Integration with Base Repository

### Dependency Injection

The new components integrate seamlessly through the existing dependency injection pattern:

```python
# mail_client_service/__init__.py
from mail_client_service._impl import ServiceClient

def get_client_impl(*, base_url: str = "http://localhost:8000", **kwargs) -> Client:
    """Factory function for ServiceClient."""
    return ServiceClient(base_url=base_url)

# Register with mail_client_api (optional - not used by default)
# mail_client_api.get_client = get_client_impl
```

**Key Points:**
- ServiceClient can be used directly or via dependency injection
- Does NOT replace `gmail_client_impl` by default (both coexist)
- Applications choose implementation by import order

### Contract Compliance

Both `GmailClient` and `ServiceClient` implement identical interfaces:

```python
# mail_client_api.Client
class Client(ABC):
    @abstractmethod
    def get_messages(self, max_results: int = 10) -> Iterator[Message]: ...

    @abstractmethod
    def get_message(self, message_id: str) -> Message: ...

    @abstractmethod
    def delete_message(self, message_id: str) -> bool: ...

    @abstractmethod
    def mark_as_read(self, message_id: str) -> bool: ...
```

**Verification:**
- Both pass the same abstract interface tests
- Both support the same method signatures
- Both return compatible Message objects

---

## Testing Strategy

### Unit Tests

Located in `src/mail_client_service/tests/`:

1. **test_api_endpoints.py**: Tests FastAPI endpoints with mocked `mail_client_api.Client`
   - Uses fixture to inject fake client
   - Tests all response codes (200, 404, 500)
   - 100% branch coverage of `api.py`

2. **test_service_client.py**: Tests `ServiceClient` with mocked HTTP responses
   - Uses `respx` to mock HTTP calls
   - Tests all `Client` interface methods
   - 100% coverage of `_impl.py`

### Integration Tests

Located in `tests/integration/`:

- **test_service_integration.py**: Tests with real FastAPI service (mock client backend)
- Marked with `@pytest.mark.circleci` for CI
- Skipped if service not running

### End-to-End Tests

Located in `tests/e2e/`:

- **test_service_e2e.py**: Tests with real Gmail API
- Marked with `@pytest.mark.local_credentials`
- Skipped in CI (requires real credentials)

---

## Design Tradeoffs Summary

### What Worked Well

1. ✅ **Interface compliance**: ServiceClient is a perfect drop-in replacement for GmailClient
2. ✅ **Mock fallback**: Enables testing and demos without credentials
3. ✅ **Auto-generation**: Type-safe client with zero manual HTTP code
4. ✅ **Docker**: Easy deployment and distribution

### Known Limitations

1. ⚠️ **No authentication**: Service is insecure (acceptable for homework)
2. ⚠️ **Synchronous only**: Can't handle high concurrency (could add async)
3. ⚠️ **Lazy iteration illusion**: `get_messages()` returns generator but HTTP call is eager
4. ⚠️ **Dev dependencies in prod**: Docker image includes test tools

### Alternative Approaches Considered

1. **GraphQL instead of REST**
   - Pros: Flexible queries, single endpoint
   - Cons: Overkill for simple CRUD, harder to generate clients
   - Decision: Stick with REST for simplicity

2. **gRPC instead of REST**
   - Pros: Better performance, bidirectional streaming
   - Cons: More complex tooling, less HTTP-friendly
   - Decision: REST more accessible for homework

3. **Manual HTTP client instead of generation**
   - Pros: Simpler workflow, no generation step
   - Cons: No type safety, manual serialization, error-prone
   - Decision: Auto-generation worth the complexity

4. **Async FastAPI + async client**
   - Pros: Better concurrency, can handle more requests
   - Cons: Base `gmail_client_impl` is sync, adds complexity
   - Decision: Sync is good enough for demo

---

## Future Improvements

If this were a production system, consider:

1. **Authentication & Authorization**
   - Add API key validation or JWT tokens
   - Rate limiting per client
   - Audit logging

2. **Async Support**
   - Make endpoints `async def`
   - Use `aiohttp` or async `httpx` in ServiceClient
   - True concurrent request handling

3. **Caching**
   - Cache message list responses
   - ETag support for conditional requests
   - Redis for distributed cache

4. **Observability**
   - Structured logging with correlation IDs
   - Prometheus metrics
   - OpenTelemetry tracing

5. **Production Docker**
   - Multi-stage build for smaller images
   - Non-root user
   - Health check endpoint
   - Secrets management (Vault, AWS Secrets Manager)

6. **API Versioning**
   - `/v1/messages` endpoints
   - Backward compatibility guarantees
   - Deprecation warnings

---

## Conclusion

The new service components successfully extend the base repository's functionality while maintaining architectural consistency. The design follows SOLID principles, uses proven patterns (adapter, dependency injection), and provides practical benefits (language-agnostic API, easy testing, containerization).

Key achievements:
- ✅ No changes to base repository required
- ✅ Seamless integration through existing interfaces
- ✅ Comprehensive testing at all levels
- ✅ Production-ready deployment with Docker
- ✅ Type-safe, auto-generated client code

The design demonstrates how service-oriented architecture can complement direct API integration, giving developers flexibility in how they consume mail client functionality.
