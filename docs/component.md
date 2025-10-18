# Component Architecture

This project demonstrates a component-based architecture with clear separation between abstract contracts and concrete implementations. The system consists of three main components that work together to provide mail client functionality.

## Project Components

### 1. `mail_client_api` - Abstract Contract
**Location:** `src/mail_client_api/`

Defines the abstract base classes (ABCs) for the mail client interface:
- `Client` - Abstract base class for mail client operations
- `Message` - Abstract base class for message objects
- Factory functions that raise `NotImplementedError` by default

**Purpose:** Provides the contract that all implementations must follow, enabling dependency injection and loose coupling.

### 2. `gmail_client_impl` - Gmail Implementation
**Location:** `src/gmail_client_impl/`

Concrete implementation using the Google Gmail API:
- `GmailClient` - Implements `Client` interface
- `GmailMessage` - Implements `Message` interface
- OAuth 2.0 authentication handling
- Direct Gmail API integration

**Purpose:** Provides actual Gmail functionality while adhering to the abstract contract.

### 3. `mail_client_service` - FastAPI Service
**Location:** `src/mail_client_service/`

RESTful API wrapper around the mail client:
- FastAPI application with REST endpoints
- `ServiceClient` - HTTP client implementing `Client` interface
- `ServiceMessage` - Message wrapper for service responses
- Auto-generated API client using `openapi-python-client`
- Built-in mock client for testing without credentials

**Purpose:** Exposes mail client operations through HTTP, enabling web-based access and service-oriented architecture.

## Component Structure

### Standard Directory Layout
```
src/<component_name>/
├── pyproject.toml           # Package configuration
├── README.md                # Component documentation
├── src/<component_name>/    # Source code (for API and Gmail impl)
│   ├── __init__.py         # Public exports and DI wiring
│   └── _impl.py            # Implementation details
└── tests/                   # Component-level unit tests
```

### Service Component Layout
```
src/mail_client_service/
├── pyproject.toml           # Package configuration
├── __init__.py             # Public exports
├── _impl.py                # ServiceClient and ServiceMessage
├── api.py                  # FastAPI router and endpoints
├── main.py                 # FastAPI application entry point
├── generated/              # Auto-generated API client
└── tests/                  # Unit tests
```

## Dependency Injection Pattern

The project uses a factory-based dependency injection pattern:

1. **Abstract contracts** define factory functions that raise `NotImplementedError`
2. **Implementations** provide `get_*_impl` factory functions
3. **Registration** happens at import time by rebinding the contract's factory:
   ```python
   mail_client_api.get_client = get_client_impl
   ```

This allows switching implementations without changing client code.

## Testing Strategy

### Component-Level Tests
- Located in each component's `tests/` directory
- Test the public interface using mocks
- Isolate external dependencies
- Focus on the component's contract compliance

### Integration Tests
- Located in `tests/integration/`
- Test interactions between components
- Verify dependency injection works correctly
- May use real services or require credentials

### End-to-End Tests
- Located in `tests/e2e/`
- Test the complete system
- Require actual Gmail API credentials
- Validate real-world scenarios

## Component Communication

```
┌─────────────────────────────────────┐
│     mail_client_api (Contract)      │
│  - Client ABC                       │
│  - Message ABC                      │
└─────────────┬───────────────────────┘
              │
       ┌──────┴──────┐
       │             │
┌──────▼─────┐  ┌───▼────────────────┐
│ gmail_impl │  │  service (FastAPI) │
│            │  │  - REST endpoints  │
│ - Direct   │  │  - ServiceClient   │
│   Gmail    │  │  - Mock fallback   │
│   API      │  │                    │
└────────────┘  └────────────────────┘
```

## Building New Components

To add a new component:

1. Create directory under `src/<component_name>/`
2. Add `pyproject.toml` with package metadata
3. Implement the contract or create a new one
4. Add to workspace in root `pyproject.toml`
5. Write component-level tests
6. Document the component in its README

This architecture ensures components are self-contained, testable, and easily replaceable.
