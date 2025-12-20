# AI Client API

Abstract base class defining the contract for AI service integrations.

## Overview

This package provides the `AIClient` abstract base class (ABC) that defines a standardized interface for AI operations. Any AI service implementation (Gemini, OpenAI, Claude, etc.) must implement this interface, ensuring interoperability across the application.

## Architecture

The AI Client API follows the dependency injection pattern:

1. **Interface Definition**: `AIClient` ABC defines the contract (the "what")
2. **Implementation**: Concrete classes implement the interface (the "how")
3. **Registration**: Implementations register themselves with the API
4. **Factory**: The API provides factory functions to create instances

This pattern decouples business logic from specific AI service implementations.

## Interface

### AIClient Abstract Base Class

```python
from abc import ABC, abstractmethod

class AIClient(ABC):
    @abstractmethod
    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict | None = None,
    ) -> str | dict:
        """Generate AI response from user input."""
        pass
```

### Method: generate_response

Generates a response from the AI service based on user input.

**Parameters:**
- `user_input` (str): The user's message or query
- `system_prompt` (str | None): Optional system instructions for the AI
- `response_schema` (dict | None): Optional JSON schema for structured output

**Returns:**
- `str | dict`: AI-generated response, either as plain text or structured data

## Usage

### Implementing the Interface

```python
from ai_client_api import AIClient

class MyAIClient(AIClient):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict | None = None,
    ) -> str | dict:
        # Implementation using your AI service
        response = call_my_ai_service(
            user_input,
            system_prompt,
            response_schema
        )
        return response
```

### Registering an Implementation

```python
import ai_client_api

# Register your implementation
ai_client_api.register_client("myai", MyAIClient)

# Get an instance
client = ai_client_api.get_client(
    provider="myai",
    api_key="your-api-key"
)
```

### Using the Client

```python
# Simple text generation
response = client.generate_response(
    user_input="What is the capital of France?",
    system_prompt="You are a helpful geography assistant."
)

# Structured output
response = client.generate_response(
    user_input="List 3 colors",
    response_schema={
        "type": "array",
        "items": {"type": "string"}
    }
)
# Returns: ["red", "blue", "green"]
```

## Available Implementations

- **gemini_client_impl**: Google Gemini AI implementation

To use other AI services, implement the `AIClient` interface and register your implementation.

## Design Principles

### Interface Stability

The `AIClient` interface is designed to remain stable. New features should be added via optional parameters to maintain backward compatibility.

### Provider Agnostic

Business logic should depend only on the `AIClient` interface, never on specific implementations. This enables:

- Easy switching between AI providers
- A/B testing different models
- Graceful fallback to alternative services

### Structured Output Support

The optional `response_schema` parameter enables type-safe structured output:

```python
# Extract entities
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
    response_schema=schema
)
# Returns: {"name": "John", "age": 30, "city": "Paris"}
```

## Testing

Implementations should provide their own test suites. Mock the `AIClient` interface for testing code that depends on it:

```python
from unittest.mock import Mock

mock_client = Mock(spec=AIClient)
mock_client.generate_response.return_value = "Mock response"

# Use in tests
result = mock_client.generate_response("test input")
assert result == "Mock response"
```
