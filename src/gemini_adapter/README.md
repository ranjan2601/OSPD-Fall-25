# Gemini Adapter

Adapter connecting the AIClient interface to the Gemini FastAPI service via HTTP client.

## Overview

This package provides an adapter that implements the `AIClient` interface while delegating HTTP calls to the auto-generated Gemini service client. It enables using the Gemini service over HTTP while maintaining compatibility with the abstract AI interface.

## Architecture

The adapter follows the adapter pattern:

1. **Interface**: Implements `AIClient` from `ai_client_api`
2. **HTTP Client**: Uses auto-generated client from `gemini_ai_service_client`
3. **Translation**: Converts between interface calls and HTTP requests

This design allows code that depends on `AIClient` to transparently use a remote Gemini service instead of a direct API client.

## Use Cases

### Local Development with Remote Service

Run the Gemini service separately and connect to it via HTTP:

```python
from gemini_adapter import GeminiServiceAdapter

# Connect to local service
adapter = GeminiServiceAdapter(base_url="http://localhost:8000")

response = adapter.generate_response(
    user_input="What is Python?",
    system_prompt="You are a helpful assistant."
)
print(response)
```

### Microservices Architecture

In a microservices setup, the adapter enables service-to-service AI calls:

```python
# Service A calls Service B's Gemini service
adapter = GeminiServiceAdapter(base_url="http://gemini-service:8000")

result = adapter.generate_response(
    user_input="Analyze this data",
    system_prompt="You are a data analyst.",
    response_schema={
        "type": "object",
        "properties": {
            "sentiment": {"type": "string"},
            "confidence": {"type": "number"}
        }
    }
)
# Returns: {"sentiment": "positive", "confidence": 0.95}
```

### Testing with Mock Service

Use the adapter with a test server for integration testing:

```python
from gemini_adapter import GeminiServiceAdapter

# Point to test server
adapter = GeminiServiceAdapter(base_url="http://test-server:8000")

# Test your code without hitting the real Gemini API
response = adapter.generate_response(
    user_input="test input",
    system_prompt="test prompt"
)
```

## Implementation Details

### GeminiServiceAdapter Class

```python
class GeminiServiceAdapter(AIInterface):
    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        """Initialize adapter with service URL."""

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate response via HTTP call to Gemini service."""
```

### HTTP Communication

The adapter:
1. Creates a `GenerateResponseRequest` model
2. Calls `client.generate_response_generate_post(body=request)`
3. Extracts the response output
4. Returns string or dict based on response type

### Type Handling

The adapter handles type conversion:
- String responses → returned as `str`
- Dict responses → returned as `dict[str, Any]`
- Maintains compatibility with `AIClient` return type

## Error Handling

The adapter validates inputs and raises:
- `ValueError`: If `user_input` or `system_prompt` is empty
- HTTP errors are propagated from the underlying client

## Dependencies

- `ai_client_api`: Abstract interface definition
- `gemini_ai_service_client`: Auto-generated HTTP client for Gemini service

## Comparison: Adapter vs Direct Client

### GeminiServiceAdapter (HTTP)
- Connects to remote Gemini service
- Network overhead
- Enables microservices architecture
- Service can be deployed independently
- Easier horizontal scaling

### GeminiClient (Direct API)
- Calls Google Gemini API directly
- Lower latency
- Simpler single-service architecture
- Requires API key in each service
- Scales vertically

## Configuration

### Base URL

Configure the service URL:

```python
# Local development
adapter = GeminiServiceAdapter(base_url="http://localhost:8000")

# Production
adapter = GeminiServiceAdapter(base_url="https://gemini-api.example.com")

# Docker Compose
adapter = GeminiServiceAdapter(base_url="http://gemini-service:8000")
```

### Default Configuration

If no `base_url` is provided, defaults to `http://127.0.0.1:8000`.

## Testing

Run tests with pytest:

```bash
pytest src/gemini_adapter/tests/
```

The test suite includes:
- Unit tests with mocked HTTP client
- Integration tests with live service
- Error handling tests
- Type conversion tests

## Design Principles

### Transparency

Clients using `AIClient` can't tell whether they're using a direct implementation or an HTTP adapter. The interface remains identical.

### Separation of Concerns

The adapter handles only HTTP communication and type conversion. Business logic remains in the service layer.

### Fail-Fast Validation

Input validation happens before making HTTP calls to catch errors early and reduce network overhead.
