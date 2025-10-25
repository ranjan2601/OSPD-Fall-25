# Gemini Service

FastAPI service that exposes AI chat functionality using Google Gemini API over HTTP endpoints.

## Overview

This service provides a RESTful API for interacting with Google's Gemini AI model. It handles:
- Sending messages and receiving AI responses
- Managing conversation history per user
- OAuth 2.0 authentication flow with Google
- Secure credential storage and token refresh

## Architecture

The service follows the component-based architecture pattern:
- Uses `gemini_impl` for concrete Gemini API integration
- Implements OAuth 2.0 flow for user authentication
- Exposes all functionality defined in `gemini_api` abstract interface
- Provides mock client fallback for testing without credentials

## Endpoints

### Chat Operations

#### Send Message
```http
POST /chat
Content-Type: application/json

{
  "user_id": "user123",
  "message": "Hello, AI!"
}
```

Response:
```json
{
  "response": "Hello! How can I help you today?"
}
```

#### Get Conversation History
```http
GET /history/{user_id}
```

Response:
```json
{
  "user_id": "user123",
  "messages": [
    {
      "role": "user",
      "content": "Hello, AI!"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    }
  ]
}
```

#### Clear Conversation
```http
DELETE /history/{user_id}
```

Response:
```json
{
  "user_id": "user123",
  "success": true
}
```

### OAuth 2.0 Authentication

#### Get Authorization URL
```http
GET /auth/login?user_id=user123
```

Response:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

#### Handle OAuth Callback
```http
POST /auth/callback
Content-Type: application/json

{
  "user_id": "user123",
  "code": "authorization_code_from_google"
}
```

Response:
```json
{
  "user_id": "user123",
  "status": "authenticated"
}
```

#### Revoke Credentials
```http
DELETE /auth/{user_id}
```

Response:
```json
{
  "user_id": "user123",
  "status": "revoked"
}
```

### Health Check

#### Root
```http
GET /
```

#### Health
```http
GET /health
```

## Configuration

Set these environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `GOOGLE_CREDENTIALS_FILE`: Path to OAuth credentials JSON (default: `credentials.json`)
- `GEMINI_DB_PATH`: Path to SQLite database for storing conversations and tokens (default: `conversations.db`)

## Running Locally

```bash
# Install dependencies
uv sync

# Set environment variables
export GEMINI_API_KEY="your-api-key"
export GOOGLE_CREDENTIALS_FILE="path/to/credentials.json"

# Run the service
uv run uvicorn gemini_service.main:app --reload --port 8001

# Access the interactive API docs
open http://localhost:8001/docs
```

## Testing

```bash
# Run all tests
uv run pytest src/gemini_service/tests/ -v

# Run with coverage
uv run pytest src/gemini_service/tests/ --cov=src/gemini_service --cov-report=term
```

## Dependencies

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `gemini-api`: Abstract interface
- `gemini-impl`: Concrete Gemini implementation with OAuth

## OAuth 2.0 Flow

1. User requests authorization URL via `GET /auth/login?user_id=<user_id>`
2. Service generates Google OAuth URL and returns it
3. User is redirected to Google for authentication
4. Google redirects back with authorization code
5. Client posts code to `POST /auth/callback`
6. Service exchanges code for credentials and stores them securely
7. Subsequent requests use stored credentials automatically

## Development

The service uses dependency injection to allow easy testing and mocking. All endpoints are tested with FastAPI's `TestClient` and mock dependencies.

Run quality checks:
```bash
# Linting
uv run ruff check src/gemini_service

# Type checking
uv run mypy src/gemini_service
```

