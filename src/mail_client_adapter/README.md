# Mail Client Adapter

HTTP service adapter implementing the `mail_client_api.Client` protocol.

## Overview

This package provides a concrete implementation of the `mail_client_api.Client` protocol that communicates with the `mail_client_service` over HTTP. This is the **adapter** that makes the remote service feel like a local library.

## Purpose

The adapter is the key to achieving the course goal: **"the consumer of your functionality should be clueless as to whether they are using a local library or a remote service."**

With this adapter, you can replace:
```python
from gmail_client_impl import get_client
client = get_client()
```

With:
```python
from mail_client_adapter import ServiceClient
client = ServiceClient(base_url="http://localhost:8000")
```

And your code continues to work without any changes! The adapter implements the same `mail_client_api.Client` interface.

## Architecture

```
Application Code
      ↓
mail_client_api.Client (protocol/interface)
      ↓
mail_client_adapter.ServiceClient (this package)
      ↓
mail_client_service_client (auto-generated HTTP client)
      ↓
HTTP Network
      ↓
mail_client_service (FastAPI server)
      ↓
gmail_client_impl (actual Gmail API)
```

## Dependencies

- `mail-client-api` - Protocol definition (workspace dependency)
- `mail-client-service-client` - Auto-generated HTTP client (workspace dependency)

## Usage

### Basic Usage

```python
from mail_client_adapter import ServiceClient

# Create a client pointing to your service
client = ServiceClient(base_url="http://localhost:8000")

# Use it just like gmail_client_impl
messages = client.get_messages(max_results=10)
for msg in messages:
    print(f"{msg.subject} from {msg.from_}")

# Get a specific message
message = client.get_message("msg123")
print(message.body)

# Mark as read
client.mark_as_read("msg123")

# Delete a message
client.delete_message("msg123")
```

### Drop-in Replacement

The adapter can be used as a drop-in replacement for `gmail_client_impl`:

```python
# Before (using local library):
import gmail_client_impl
from mail_client_api import get_client
client = get_client()  # Returns gmail_client_impl.GmailClient

# After (using remote service):
from mail_client_adapter import ServiceClient
client = ServiceClient(base_url="http://localhost:8000")

# Rest of your code stays the same!
messages = list(client.get_messages())
```

## Components

### ServiceClient

The main adapter class that implements `mail_client_api.Client`:

- **get_messages(max_results: int)** → Iterator[Message]
- **get_message(message_id: str)** → Message
- **mark_as_read(message_id: str)** → bool
- **delete_message(message_id: str)** → bool

### ServiceMessage

A message implementation that wraps responses from the auto-generated client and implements the `mail_client_api.Message` protocol.

## Testing

Run the adapter tests:

```bash
pytest src/mail_client_adapter/tests/
```

## Notes

- This is a **library/component**, not a service. Import and use it in your Python code.
- The adapter hides all network complexity from the consumer.
- Requires the `mail_client_service` to be running at the specified `base_url`.
- Implements the same interface as `gmail_client_impl`, so code using `mail_client_api.Client` works with both.

## Design Pattern

This package implements the **Adapter Pattern**: it adapts the auto-generated HTTP client to match the `mail_client_api.Client` interface, allowing seamless integration with existing code.
