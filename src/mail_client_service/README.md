# Mail Client Service

## Overview

The `mail_client_service` package provides a FastAPI-based REST API wrapper around the mail client functionality. It includes both the service implementation (server) and an HTTP client that communicates with the service.

## Purpose

This package serves dual purposes:

- **REST API Service**: FastAPI application exposing mail client operations through HTTP endpoints
- **HTTP Client**: ServiceClient class implementing `mail_client_api.Client` interface to communicate with the service
- **Mock Fallback**: Built-in MockClient for testing without Gmail credentials
- **Docker Support**: Containerized deployment using Docker

## Architecture

### Components

1. **FastAPI Service** (`api.py`, `main.py`)
   - REST endpoints for mail operations
   - Automatic mock client fallback
   - OpenAPI schema generation

2. **ServiceClient** (`_impl.py`)
   - Implements `mail_client_api.Client` interface
   - Uses auto-generated HTTP client
   - Communicates with service over HTTP

3. **Auto-Generated Client** (`generated/`)
   - Generated from OpenAPI schema
   - Type-safe HTTP client
   - Handles request/response serialization

## REST API Endpoints

### Root Endpoint
```http
GET /
```
Returns service health check.

### List Messages
```http
GET /messages?max_results=10
```
Fetches messages from inbox.

### Get Message
```http
GET /messages/{message_id}
```
Retrieves a specific message.

### Delete Message
```http
DELETE /messages/{message_id}
```
Deletes a message.

### Mark as Read
```http
POST /messages/{message_id}/mark-as-read
```
Marks a message as read.

## Running the Service

### Locally with uvicorn
```bash
uv run uvicorn src.mail_client_service.main:app --reload
```

The service will be available at `http://localhost:8000`

### With Docker
```bash
# Build the image
docker build -t mail-client-service .

# Run the container
docker run -d -p 8000:8000 --name mail-service mail-client-service

# Test the service
curl http://localhost:8000/
curl http://localhost:8000/messages

# Stop the container
docker stop mail-service && docker rm mail-service
```

### Access Documentation
- **OpenAPI docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Using the ServiceClient

### Basic Usage
```python
from mail_client_service import ServiceClient

# Connect to local service
client = ServiceClient("http://localhost:8000")

# Use like any other mail client
for message in client.get_messages(max_results=5):
    print(f"From: {message.from_}")
    print(f"Subject: {message.subject}")
```

### With Dependency Injection
```python
import mail_client_service
from mail_client_api import get_client

# ServiceClient automatically registered
client = get_client(base_url="http://localhost:8000")
messages = client.get_messages(max_results=10)
```

## Mock Client

When no Gmail credentials are available, the service automatically uses a built-in MockClient that provides three test messages:

- **Message 1**: Test Email 1
- **Message 2**: Test Email 2
- **Message 3**: Test Email 3

This enables:
- Development without Gmail API access
- Testing service endpoints
- CI/CD pipeline execution

## Client Generation

The HTTP client is auto-generated from the OpenAPI schema using `openapi-python-client`.

### Regenerating the Client

```bash
# 1. Start the service
uv run uvicorn src.mail_client_service.main:app

# 2. Generate OpenAPI schema
curl http://localhost:8000/openapi.json > openapi_schema.json

# 3. Regenerate client
cd src/mail_client_service
openapi-python-client generate --path openapi_schema.json --output-path generated
```

## Service Message Implementation

The `ServiceMessage` class wraps API responses and implements the `Message` protocol:

```python
class ServiceMessage(message.Message):
    """Message implementation for service responses."""

    @property
    def id(self) -> str:
        return self._response.id

    @property
    def from_(self) -> str:
        return self._response.from_

    @property
    def subject(self) -> str:
        return self._response.subject

    @property
    def body(self) -> str:
        return self._response.body

    # Additional properties: to, date
```

## Testing

### Unit Tests
```bash
# Test service endpoints
uv run pytest src/mail_client_service/tests/ -q

# With coverage
uv run pytest src/mail_client_service/tests/ --cov=src/mail_client_service --cov-report=term-missing
```

### Integration Tests
```bash
# Requires running service
uv run pytest tests/integration/test_service_integration.py
```

## Dependencies

**Production:**
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `httpx`: HTTP client
- `pydantic`: Data validation

**Development:**
- `openapi-python-client`: Client generation
- `pytest`: Testing framework

## Deployment

### Docker Deployment

The service includes a `Dockerfile` for containerized deployment:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
RUN uv sync --frozen --all-packages --extra dev
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.mail_client_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run:**
```bash
docker build -t mail-client-service .
docker run -d -p 8000:8000 mail-client-service
```

### Environment Variables

Set these for Gmail API access (optional, falls back to mock):
- `GMAIL_CLIENT_ID`
- `GMAIL_CLIENT_SECRET`
- `GMAIL_REFRESH_TOKEN`

## Architecture Benefits

### Service-Based Approach
- **Separation of Concerns**: API logic separated from business logic
- **Scalability**: Can scale service independently
- **Language Agnostic**: Any HTTP client can consume the API
- **Centralized Logic**: Single point for mail operations

### Client Interface Compliance
- **Drop-in Replacement**: Same interface as GmailClient
- **Transparent Usage**: Switching between local and service is just geography
- **Type Safety**: Auto-generated client with full type hints
