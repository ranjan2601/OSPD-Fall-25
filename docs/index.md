# Welcome to the Mail & Gemini AI Client Project

This project demonstrates a professional-grade, component-based architecture for a modern Python application with two main services:

1. **Mail Client Service** - Interact with Gmail API through a direct client and FastAPI service
2. **Gemini AI Service** - Chat with Google's Gemini AI model with conversation history and OAuth authentication

## Quick Start

### Installation
```bash
# Install dependencies
uv sync --all-packages --extra dev

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
```

### Run the Services

**Mail Client Service:**
```bash
uv run uvicorn mail_client_service.main:app --reload
```

**Gemini AI Service:**
```bash
uv run uvicorn gemini_service.main:app --reload
```

**Combined Service (Fly.io Deployment):**
```bash
uv run python src/app.py
```

### Run Tests
```bash
# Unit tests only
uv run pytest src/

# All CI-compatible tests
uv run pytest src/ tests/ -m "not local_credentials"

# With coverage report
uv run pytest src/ --cov --cov-report=html
```

## Project Components

### HW1 - Mail Client Components
1. **`mail_client_api`** - Abstract base classes defining the mail client interface
2. **`gmail_client_impl`** - Gmail-specific implementation using Google API
3. **`mail_client_service`** - FastAPI service with dependency injection and REST endpoints
4. **`mail_client_service_client`** - Auto-generated HTTP client for the service
5. **`mail_client_adapter`** - Adapter implementing `mail_client_api.Client` using the HTTP service

### HW2 - Gemini AI Components
1. **`gemini_api`** - Abstract base classes for AI client interface (send message, get history, clear conversation)
2. **`gemini_impl`** - Google Gemini API implementation with SQLite conversation storage
3. **`gemini_service`** - FastAPI service with OAuth 2.0 authentication and per-user API key management
4. **`gemini_service_api_client`** - Auto-generated HTTP client for the service
5. **`gemini_adapter`** - Adapter implementing `gemini_api.AIClient` interface via HTTP

## Key Features

- **Clean Architecture** - Separation of concerns with abstract contracts and concrete implementations
- **Dependency Injection** - Factory-based DI pattern for loose coupling and easy testing
- **Type Safety** - Strict mypy checking across all modules
- **Component-Based** - Self-contained packages with minimal inter-dependencies
- **OAuth 2.0** - Secure authentication for Gemini AI service
- **Comprehensive Testing** - Unit, integration, and E2E tests with 80%+ code coverage
- **Production Ready** - Deployed to Fly.io with SQLite persistence

This documentation provides detailed information about the architecture, API contracts, testing strategies, and usage guidelines.
