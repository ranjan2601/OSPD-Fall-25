# Mail Client API

## Overview

The `mail_client_api` package defines the core **Client** protocol (interface) for email client operations. This package serves as the foundational contract for all mail client implementations in the email assistant system.

As a pure interface package, it contains no concrete implementations—only the protocol definition and factory function that will be injected by concrete implementations at runtime.

## Purpose

This package establishes the **"what"** of mail client operations without any **"how"**. It defines:

- The operations every mail client must support (retrieve, delete, mark as read)
- The contract that all client implementations must fulfill  
- A factory function for creating client instances through dependency injection
- The integration point with the Message protocol for type safety

## Architecture

### Component Design

The Client protocol follows **single responsibility principle**, focusing exclusively on core email operations:

- **Message Retrieval**: Get individual messages or iterate through inbox
- **Message Management**: Delete messages and update read status
- **Batch Operations**: Efficiently handle multiple messages with configurable limits

### Protocol Integration

The Client protocol is tightly integrated with the Message protocol:

```python
from mail_client_api import Client, get_client
from message import Message

client = get_client()
messages = client.get_messages(max_results=5)
for message in messages:  # Each message conforms to Message protocol
    print(f"Subject: {message.subject}")
```

### Dependency Injection

The package uses a factory function pattern with dependency injection:

```python
from mail_client_api import get_client

# The concrete implementation is injected at runtime
client = get_client(interactive=False)
```

When a concrete implementation package (like `gmail_client_impl`) is imported, it automatically overrides the `get_client` function.

## API Reference

### Client Protocol

```python
@runtime_checkable
class Client(Protocol):
    """A protocol representing a mail client for email operations."""
```

#### Methods

##### `get_message(message_id: str) -> Message`
Retrieve a single message by its unique identifier.

**Parameters:**
- `message_id`: The unique ID of the message to retrieve

**Returns:**
- `Message`: The message object corresponding to the given ID

**Usage:**
```python
message = client.get_message("12345")
print(f"Subject: {message.subject}")
```

##### `delete_message(message_id: str) -> bool`
Delete a message by its unique identifier.

**Parameters:**
- `message_id`: The unique ID of the message to delete

**Returns:**
- `bool`: True if successfully deleted, False otherwise

**Usage:**
```python
if client.delete_message("12345"):
    print("Message deleted successfully")
```

##### `mark_as_read(message_id: str) -> bool`
Mark a message as read by its unique identifier.

**Parameters:**
- `message_id`: The unique ID of the message to mark as read

**Returns:**
- `bool`: True if successfully marked as read, False otherwise

**Usage:**
```python
if client.mark_as_read("12345"):
    print("Message marked as read")
```

##### `get_messages(max_results: int = 10) -> Iterator[Message]`
Retrieve multiple messages from the inbox as an iterator.

**Parameters:**
- `max_results`: Maximum number of messages to return (default: 10)

**Returns:**
- `Iterator[Message]`: Iterator yielding Message objects

**Usage:**
```python
# Get latest 20 messages
for message in client.get_messages(max_results=20):
    print(f"From: {message.from_} - Subject: {message.subject}")
```

### Factory Function

```python
def get_client(interactive: bool = False) -> Client:
    """Return an instance of a Mail Client implementation.
    
    Args:
        interactive: If True, may prompt for user input during initialization
                    If False, uses environment variables or other non-interactive methods
        
    Returns:
        Client: A concrete mail client instance
        
    Raises:
        NotImplementedError: If no implementation has been registered
    """
```

## Usage Examples

### Basic Operations

```python
from mail_client_api import get_client

# Get client instance (implementation injected at runtime)
client = get_client(interactive=False)

# Retrieve and process messages
messages = client.get_messages(max_results=10)
for message in messages:
    print(f"ID: {message.id}")
    print(f"From: {message.from_}")
    print(f"Subject: {message.subject}")
    print(f"Date: {message.date}")
    print("---")
```

### Message Management

```python
from mail_client_api import get_client

client = get_client()

# Get a specific message
message = client.get_message("important_msg_123")

# Mark it as read
if client.mark_as_read(message.id):
    print(f"Marked '{message.subject}' as read")

# Delete if needed
if message.subject.startswith("SPAM"):
    if client.delete_message(message.id):
        print("Spam message deleted")
```

### Batch Processing

```python
from mail_client_api import get_client

client = get_client()

# Process all messages in batches
def process_inbox():
    processed_count = 0
    for message in client.get_messages(max_results=50):
        # Process each message
        print(f"Processing: {message.subject}")
        
        # Mark as read after processing
        client.mark_as_read(message.id)
        processed_count += 1
    
    print(f"Processed {processed_count} messages")

process_inbox()
```

### Error Handling

```python
from mail_client_api import get_client

try:
    client = get_client()
    message = client.get_message("non_existent_id")
except Exception as e:
    print(f"Error retrieving message: {e}")
```

## Implementation Requirements

To create a concrete mail client implementation:

1. **Implement the Protocol**: Create a class that implements all Client methods
2. **Override the Factory**: Replace `mail_client_api.get_client` with your implementation  
3. **Handle Authentication**: Implement appropriate authentication for your mail service
4. **Message Integration**: Ensure your methods return objects conforming to the Message protocol

Example implementation structure:

```python
# In your implementation package
import mail_client_api
from .concrete_client import ConcreteClient

def get_client_impl(interactive: bool = False) -> mail_client_api.Client:
    return ConcreteClient(interactive=interactive)

# Dependency injection
mail_client_api.get_client = get_client_impl
```

## Testing

### Running Tests

```bash
# Run unit tests for this component
uv run pytest src/mail_client_api/tests/ -v

# Run with coverage
uv run pytest src/mail_client_api/tests/ --cov=src/mail_client_api --cov-report=term-missing

# Run integration tests (requires implementation)
uv run pytest tests/integration/ -k mail_client -v
```

### Test Categories

- **Unit Tests**: Located in `tests/` - validate protocol definition and factory function
- **Integration Tests**: Located in `../../tests/integration/` - test with concrete implementations
- **Type Tests**: Verify protocol conformance and type checking behavior

## Dependencies

### Required Dependencies

- **[message](../message/README.md)**: This package depends on the Message protocol for type annotations and return types

### External Dependencies

This package has **no external dependencies** beyond Python's standard library, the `typing` module, and the `message` protocol package. This keeps the interface pure and implementation-agnostic.

## Related Components

- **[gmail_client_impl](../gmail_client_impl/README.md)**: Gmail-specific implementation of the Client protocol
- **[message](../message/README.md)**: Message protocol used by Client methods
- **[gmail_message_impl](../gmail_message_impl/README.md)**: Typically used together with Gmail client implementation

## Design Principles

This package exemplifies several key design principles:

- **Single Responsibility**: Defines only mail client operations, nothing else
- **Open/Closed**: Open for extension via implementations, closed for modification
- **Dependency Inversion**: High-level code depends on this abstraction, not concrete implementations
- **Interface Segregation**: Contains only essential client operations, no unnecessary complexity
- **Composition**: Composes with Message protocol rather than reimplementing message functionality

## Authentication Design

The `interactive` parameter in `get_client()` provides flexibility for different authentication scenarios:

- **Interactive Mode** (`interactive=True`): Suitable for development, allows OAuth flows with browser interaction
- **Non-Interactive Mode** (`interactive=False`): Suitable for CI/CD, servers, uses environment variables or pre-stored tokens

This design ensures the same client interface works across development, testing, and production environments.