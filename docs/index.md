# Welcome to the Mail Client Project

This project demonstrates a professional-grade, component-based architecture for a modern Python application that interacts with the Gmail API through both a direct client and a FastAPI service.

## Quick Start

### Installation
```bash
# Install dependencies
uv sync --all-packages --extra dev

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
```

### Run the FastAPI Server
```bash
# Option 1: Run locally
uv run uvicorn mail_client_service.main:app --reload

# Option 2: Run with Docker
docker build -t mail-client-service .
docker run -d -p 8000:8000 --name mail-service mail-client-service
```

### Run Tests
```bash
# Unit tests only
uv run pytest src/

# All CI-compatible tests
uv run pytest src/ tests/ -m "not local_credentials"
```

## Project Components

This project consists of five main packages:

1. **`mail_client_api`** - Abstract base classes defining the mail client interface
2. **`gmail_client_impl`** - Gmail-specific implementation using Google API
3. **`mail_client_service`** - FastAPI service with dependency injection and REST endpoints
4. **`mail_client_service_client`** - Auto-generated HTTP client for the service
5. **`mail_client_adapter`** - Adapter implementing `mail_client_api.Client` using the HTTP service

This documentation provides detailed information about the architecture, API contracts, and usage guidelines.
