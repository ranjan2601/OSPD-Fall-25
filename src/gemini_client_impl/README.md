# Gemini Client Implementation

Google Gemini API implementation of the AIClient abstract base class.

## Overview

This package provides the `GeminiClient` class, a concrete implementation of the `AIClient` interface that integrates with Google's Gemini API. It supports both conversational responses and structured output using JSON schemas.

## Architecture

The implementation follows the dependency injection pattern:

1. **Interface Compliance**: Implements the `AIClient` ABC from `ai_client_api`
2. **Registration**: Provides a `register()` function to register itself with the API
3. **Factory Pattern**: Returns instances through the `ai_client_api.get_client()` factory

This ensures that business logic depends only on the stable `AIClient` interface, not on Gemini-specific details.

## Features

### Conversational Mode

Generate natural language responses without structured output:

```python
import ai_client_api
import gemini_client_impl

gemini_client_impl.register()

client = ai_client_api.get_client(api_key="your-gemini-api-key")

response = client.generate_response(
    user_input="What is machine learning?",
    system_prompt="You are a helpful AI assistant."
)
# Returns: "Machine learning is a subset of artificial intelligence..."
```

### Structured Output Mode

Generate structured data conforming to a JSON schema:

```python
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "number"},
        "city": {"type": "string"}
    }
}

response = client.generate_response(
    user_input="John is 30 years old and lives in Paris",
    system_prompt="Extract person information",
    response_schema=schema
)
# Returns: {"name": "John", "age": 30, "city": "Paris"}
```

## Implementation Details

### GeminiClient Class

The `GeminiClient` class implements the `AIClient` interface:

```python
class GeminiClient(AIInterface):
    def __init__(self, api_key: str) -> None:
        """Initialize with Gemini API key."""

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate response using Gemini API."""
```

### Model Configuration

- **Model**: Uses `gemini-3-flash-preview` by default
- **Conversational Mode**: Returns plain text responses
- **Structured Mode**: Configures `response_mime_type="application/json"` with the provided schema

### Error Handling

The implementation raises:
- `ValueError`: If `user_input` or `system_prompt` is empty
- `RuntimeError`: If the Gemini API call fails

## Registration

To use this implementation, register it with the `ai_client_api`:

```python
import gemini_client_impl

gemini_client_impl.register()
```

After registration, `ai_client_api.get_client(api_key=...)` will return `GeminiClient` instances.

## Dependencies

- `ai_client_api`: Abstract interface definition
- `google-generativeai`: Google's Gemini API client library

## Testing

Run tests with pytest:

```bash
pytest src/gemini_client_impl/tests/
```

The test suite includes:
- Unit tests with mocked Gemini API calls
- Validation tests for input parameters
- Tests for both conversational and structured output modes
- Error handling tests

## API Key Management

The API key must be a valid Google Gemini API key. Obtain one from [Google AI Studio](https://makersuite.google.com/app/apikey).

Store the key securely:
- Environment variables: `GEMINI_API_KEY`
- Configuration files (excluded from version control)
- Secret management systems for production

## Design Principles

### Interface Compliance

The implementation strictly adheres to the `AIClient` interface contract, ensuring compatibility with any code that depends on the abstract interface.

### Minimal Dependencies

Only depends on the abstract interface and the Gemini SDK, avoiding unnecessary coupling to other implementation details.

### Type Safety

Fully typed with mypy-compliant type annotations for static analysis and IDE support.
