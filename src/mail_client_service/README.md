# Mail Client Service

## Overview

The `mail_client_service` package provides an auto-generated HTTP client that implements the `mail_client_api.Client` protocol. This client communicates with a FastAPI mail service over HTTP while maintaining the same interface as the direct Gmail implementation.

## Purpose

This package enables service-based mail client operations:

- **HTTP Client Generation**: Auto-generated from OpenAPI schema
- **Protocol Compliance**: Implements the same Client interface as Gmail client
- **Transparent Usage**: Drop-in replacement for direct Gmail client
- **Network Communication**: Handles HTTP requests/responses to mail service

## Architecture

### Auto-Generation Strategy

1. **Schema-Based Generation**: Uses openapi-python-client to generate HTTP client from service schema
2. **Wrapper Implementation**: ServiceClient class wraps auto-generated client 
3. **Protocol Translation**: Maps Client protocol methods to HTTP endpoints
4. **Response Mapping**: Converts HTTP responses back to Message protocol objects

### Client Methods

- `get_messages(max_results)` → `GET /messages?max_results=N`
- `get_message(message_id)` → `GET /messages/{message_id}`
- `delete_message(message_id)` → `DELETE /messages/{message_id}`
- `mark_as_read(message_id)` → `PUT /messages/{message_id}/read`

## Client Generation

The HTTP client is auto-generated from an OpenAPI schema using the `openapi-python-client` package. This ensures the client stays in sync with the service API.

### Regenerating the Client

To regenerate the client from the schema (without needing a running service):

```bash
# Using the provided script
python regenerate_client.py

# Or manually
cd src/mail_client_service
openapi-python-client generate --path openapi_schema.json --output-path generated
```

The OpenAPI schema is stored in `openapi_schema.json` and defines the mail service API endpoints.

## Usage

### Basic Usage

```python
import mail_client_service
from mail_client_api import get_client

# Uses service client with default configuration
client = get_client()
messages = client.get_messages(max_results=10)
```

### Custom Service URL

```python
import mail_client_service
from mail_client_api import get_client

# Configure service URL
client = get_client(base_url="http://my-service:8080")
messages = client.get_messages(max_results=5)
```

### Same Interface as Gmail Client

```python
# This code works identically with both Gmail client and service client
client = get_client()

# Fetch messages
for message in client.get_messages(max_results=5):
    print(f"From: {message.from_}")
    print(f"Subject: {message.subject}")
    
    # Mark as read
    client.mark_as_read(message.id)

# Get specific message
message = client.get_message("msg_123")
print(f"Body: {message.body}")

# Delete message
success = client.delete_message("spam_msg_456")
```

## Service Message Implementation

The package includes a `ServiceMessage` class that implements the `Message` protocol by wrapping the auto-generated response models:

```python
class ServiceMessage(message.Message):
    """Message implementation for service responses."""
    
    @property
    def id(self) -> str: ...
    
    @property
    def from_(self) -> str: ...
    
    # ... other Message protocol properties
```

## Dependencies

- `httpx>=0.25.0`: HTTP client for making requests
- `pydantic>=2.0.0`: Data validation and serialization
- `openapi-python-client>=0.15.0`: Auto-generation tool

## Integration

The service client automatically integrates with the existing mail client system through dependency injection. When the package is imported, it overrides the `mail_client_api.get_client` factory function, making the service client the default implementation.

This allows existing code to switch between local Gmail client and service client simply by changing imports:

```python
# Use Gmail client directly
import gmail_client_impl
from mail_client_api import get_client
client = get_client()  # Returns GmailClient

# Use service client
import mail_client_service
from mail_client_api import get_client  
client = get_client()  # Returns ServiceClient
```

The choice between local and service-based operations becomes "just geography" - the interface remains identical.
