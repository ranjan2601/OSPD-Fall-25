# Gemini AI Service Client

Auto-generated HTTP client for the Gemini AI Service API.

## Overview

This package is an auto-generated client library for accessing the Gemini AI Service over HTTP. It provides type-safe Python bindings for all service endpoints, automatically generated from the OpenAPI specification.

## Generation

This client is generated using `openapi-python-client` from the FastAPI service's OpenAPI schema. Do not manually edit the generated files.

### Regenerating the Client

To regenerate this client after API changes:

```bash
# Start the Gemini service
uv run uvicorn gemini_service.main:app --port 8000

# Generate the client from OpenAPI schema
openapi-python-client generate \
  --url http://localhost:8000/openapi.json \
  --output-path src/gemini_ai_service_client
```

## Usage

### Basic Client

```python
from gemini_ai_service_client import Client
from gemini_ai_service_client.models import GenerateResponseRequest

# Create client
client = Client(base_url="http://localhost:8000")

# Generate response
request = GenerateResponseRequest(
    user_input="What is the capital of France?",
    system_prompt="You are a helpful assistant."
)

response = client.generate_response_generate_post(body=request)
print(response.output)
```

### Authenticated Client

For services requiring authentication:

```python
from gemini_ai_service_client import AuthenticatedClient

client = AuthenticatedClient(
    base_url="http://localhost:8000",
    token="your-auth-token"
)

# Use same API methods as Client
```

### Health Check

```python
from gemini_ai_service_client import Client

client = Client(base_url="http://localhost:8000")
health = client.health_check_health_get()

print(f"Status: {health.status}")
print(f"Service: {health.service}")
```

## Available Endpoints

### generate_response_generate_post

Generate AI responses with optional structured output.

**Method**: `POST /generate`

**Request Model**: `GenerateResponseRequest`
- `user_input` (str): The user's input text
- `system_prompt` (str): System instruction for the model
- `response_schema` (dict | None): Optional JSON schema for structured output

**Response Model**: `GenerateResponseResponse`
- `output` (str | dict): AI-generated response

### health_check_health_get

Check service health status.

**Method**: `GET /health`

**Response Model**: `HealthCheckResponse`
- `status` (str): Health status
- `service` (str): Service name
- `version` (str): Service version

### read_root_get

Get service root information.

**Method**: `GET /`

**Response Model**: `dict`
- `message` (str): Service status message

## Models

All request/response models are Pydantic classes with full type safety:

### GenerateResponseRequest

```python
from gemini_ai_service_client.models import GenerateResponseRequest

request = GenerateResponseRequest(
    user_input="Hello",
    system_prompt="You are helpful.",
    response_schema={"type": "object", "properties": {...}}
)
```

### GenerateResponseResponse

```python
from gemini_ai_service_client.models import GenerateResponseResponse

response: GenerateResponseResponse = client.generate_response_generate_post(...)

# Access output
if isinstance(response.output, str):
    print(f"Text: {response.output}")
else:
    print(f"Structured: {response.output}")
```

### HealthCheckResponse

```python
from gemini_ai_service_client.models import HealthCheckResponse

health: HealthCheckResponse = client.health_check_health_get()
print(f"{health.service} is {health.status}")
```

## Error Handling

The client uses the `errors` module for HTTP error handling:

```python
from gemini_ai_service_client import Client
from gemini_ai_service_client.errors import UnexpectedStatus

client = Client(base_url="http://localhost:8000")

try:
    response = client.generate_response_generate_post(body=request)
except UnexpectedStatus as e:
    print(f"HTTP Error: {e.status_code}")
    print(f"Content: {e.content}")
```

## Type Safety

The generated client includes:
- Full mypy type annotations
- Pydantic model validation
- Type-safe response handling
- IDE autocomplete support

## Integration with Gemini Adapter

This client is used internally by `gemini_adapter`:

```python
from gemini_ai_service_client import Client as GeminiHTTPClient

class GeminiServiceAdapter:
    def __init__(self, base_url: str):
        self.client = GeminiHTTPClient(base_url=base_url)
```

The adapter wraps this client to implement the `AIClient` interface.

## Package Structure

```
gemini_ai_service_client/
├── __init__.py           # Exports Client and AuthenticatedClient
├── client.py             # HTTP client implementation
├── errors.py             # Error handling
├── types.py              # Type definitions
├── api/                  # Endpoint methods
│   └── default/
│       ├── generate_response_generate_post.py
│       ├── health_check_health_get.py
│       └── read_root_get.py
└── models/               # Request/response models
    ├── generate_response_request.py
    ├── generate_response_response.py
    ├── health_check_response.py
    └── ...
```

## Testing

The client includes generated tests. Run with pytest:

```bash
pytest src/gemini_ai_service_client/tests/
```

## Dependencies

- `httpx`: HTTP client library
- `attrs`: Class decorators
- `python-dateutil`: Date parsing

## Design Principles

### Auto-Generation

Never manually edit generated code. All changes should be made to the OpenAPI specification in the FastAPI service.

### Type Safety

The generator creates fully typed code that passes mypy strict mode checks.

### Minimal Overhead

The client is a thin wrapper around httpx with automatic serialization/deserialization.
