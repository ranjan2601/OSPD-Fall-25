# Gemini Service

FastAPI service exposing Gemini AI capabilities via HTTP endpoints.

## Overview

This package provides a REST API service that wraps the Gemini client implementation, making AI capabilities accessible over HTTP. The service follows the `AIClient` interface contract and exposes it through well-defined API endpoints.

## Architecture

The service is built on FastAPI and follows a layered architecture:

1. **HTTP Layer**: FastAPI routes and request/response models
2. **Business Logic**: Delegates to `gemini_client_impl` through `ai_client_api`
3. **Configuration**: Environment-based credential management

This design keeps the HTTP layer thin and delegates actual AI operations to the registered implementation.

## API Endpoints

### POST /generate

Generate AI responses with optional structured output.

**Request Body:**
```json
{
  "user_input": "What is the capital of France?",
  "system_prompt": "You are a helpful assistant.",
  "response_schema": null
}
```

**Response (Conversational):**
```json
{
  "output": "The capital of France is Paris."
}
```

**Request Body (Structured Output):**
```json
{
  "user_input": "Extract person info: John is 30 and lives in Paris",
  "system_prompt": "Extract structured data",
  "response_schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "age": {"type": "number"},
      "city": {"type": "string"}
    }
  }
}
```

**Response (Structured):**
```json
{
  "output": {
    "name": "John",
    "age": 30,
    "city": "Paris"
  }
}
```

### GET /health

Health check endpoint for monitoring service availability.

**Response:**
```json
{
  "status": "healthy",
  "service": "Gemini AI Service",
  "version": "1.0.0"
}
```

### GET /

Root endpoint returning service status.

**Response:**
```json
{
  "message": "Gemini AI Service is running"
}
```

## Running the Service

### Local Development

```bash
# Install dependencies
uv sync --all-packages --extra dev

# Set environment variable
export GEMINI_API_KEY="your-api-key"

# Run the service
uv run uvicorn gemini_service.main:app --reload --port 8000
```

The service will be available at `http://localhost:8000`.

### API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Docker Deployment

```bash
# Build the image
docker build -t gemini-service .

# Run the container
docker run -p 8000:8000 -e GEMINI_API_KEY="your-api-key" gemini-service
```

## Configuration

### Environment Variables

- `GEMINI_API_KEY`: Required. Google Gemini API key

The service loads configuration from a `.env` file if present.

### Credential Resolution

The service uses `ai_client_api.credential.resolve_api_key()` to obtain API keys:
- Checks environment variables
- Falls back to credential files if configured
- Raises clear errors if credentials are missing

## Error Handling

The service provides clear HTTP error responses:

- **400 Bad Request**: Invalid input (empty user_input or system_prompt)
- **500 Internal Server Error**: API key not found or Gemini API errors

Error responses include detailed messages:
```json
{
  "detail": "user_input is required"
}
```

## Dependencies

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `ai_client_api`: Abstract interface
- `gemini_client_impl`: Gemini implementation
- `python-dotenv`: Environment variable management

## Testing

Run tests with pytest:

```bash
pytest src/gemini_service/tests/
```

The test suite includes:
- Unit tests with mocked AI client
- API endpoint tests using TestClient
- Validation tests for request parameters
- Error handling tests

## Integration with Other Services

The Gemini service can be called from other services:

```python
import httpx

response = httpx.post(
    "http://localhost:8000/generate",
    json={
        "user_input": "Hello",
        "system_prompt": "You are helpful.",
        "response_schema": None
    }
)

data = response.json()
print(data["output"])
```

Or use the auto-generated client from `gemini_ai_service_client`:

```python
from gemini_ai_service_client import Client

client = Client(base_url="http://localhost:8000")
# Use client methods...
```

## Design Principles

### Thin HTTP Layer

The service is a minimal HTTP wrapper around the AI client implementation. Business logic remains in the client layer, not in the API routes.

### Interface-Based Design

The service depends on `ai_client_api`, not directly on `gemini_client_impl`. This allows swapping implementations without changing the service code.

### Standard REST Patterns

Uses standard HTTP methods, status codes, and JSON request/response formats for easy integration with other systems.
