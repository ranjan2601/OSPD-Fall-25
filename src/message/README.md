# Message Protocol

## Overview

The `message` package defines the core **Message** protocol (interface) that represents an email message with its essential properties. This package serves as the foundational contract for all message implementations in the email assistant system.

As a pure interface package, it contains no concrete implementations—only the protocol definition and factory function that will be injected by concrete implementations at runtime.

## Purpose

This package establishes the **"what"** of message representation without any **"how"**. It defines:

- The structure and properties every email message must have
- The contract that all message implementations must fulfill
- A factory function for creating message instances through dependency injection

## Architecture

### Component Design

The Message protocol follows the **Interface Segregation Principle**, defining only the essential properties needed to represent an email message:

- **Message Identity**: Unique identifier for tracking and reference
- **Communication Metadata**: Sender, recipient, and timestamp information  
- **Content Properties**: Subject and body text for message content

### Dependency Injection

The package uses a factory function pattern with dependency injection:

```python
from message import Message, get_message

# The concrete implementation is injected at runtime
message = get_message(msg_id="123", raw_data="...")
```

When a concrete implementation package (like `gmail_message_impl`) is imported, it automatically overrides the `get_message` function with its implementation.

## API Reference

### Message Protocol

```python
@runtime_checkable
class Message(Protocol):
    """A protocol representing an email message."""
```

#### Properties

- **`id: str`** - Unique identifier of the message
- **`from_: str`** - Sender's email address  
- **`to: str`** - Recipient's email address
- **`date: str`** - Date the message was sent
- **`subject: str`** - Subject line of the message
- **`body: str`** - Plain text content of the message

### Factory Function

```python
def get_message(msg_id: str, raw_data: str) -> Message:
    """Return an instance of a Message implementation.
    
    Args:
        msg_id: The unique identifier for the message
        raw_data: The raw data used to construct the message
        
    Returns:
        Message: An instance conforming to the Message protocol
    """
```

## Usage Examples

### Basic Usage

```python
from message import Message, get_message

# Get a message instance (implementation injected at runtime)
message = get_message(msg_id="12345", raw_data="base64_encoded_data")

# Access message properties
print(f"From: {message.from_}")
print(f"To: {message.to}")
print(f"Subject: {message.subject}")
print(f"Date: {message.date}")
print(f"Body: {message.body}")
```

### Type Checking

```python
from message import Message
import isinstance

def process_message(msg: Message) -> None:
    """Process any message that implements the Message protocol."""
    if isinstance(msg, Message):
        print(f"Processing message: {msg.subject}")
```

## Implementation Requirements

To create a concrete message implementation:

1. **Implement the Protocol**: Create a class that implements all Message properties
2. **Override the Factory**: Replace `message.get_message` with your implementation
3. **Handle Raw Data**: Parse the `raw_data` parameter appropriately for your message format

Example implementation structure:

```python
# In your implementation package
import message
from .concrete_message import ConcreteMessage

def get_message_impl(msg_id: str, raw_data: str) -> message.Message:
    return ConcreteMessage(msg_id=msg_id, raw_data=raw_data)

# Dependency injection
message.get_message = get_message_impl
```

## Testing

### Running Tests

```bash
# Run unit tests for this component
uv run pytest src/message/tests/ -v

# Run with coverage
uv run pytest src/message/tests/ --cov=src/message --cov-report=term-missing
```

### Test Categories

- **Unit Tests**: Located in `tests/` - validate protocol definition and factory function
- **Type Tests**: Verify protocol conformance and type checking behavior

## Dependencies

This package has **no external dependencies** beyond Python's standard library and the `typing` module. This is intentional to keep the interface pure and implementation-agnostic.

## Related Components

- **[gmail_message_impl](../gmail_message_impl/README.md)**: Gmail-specific implementation of the Message protocol
- **[mail_client_api](../mail_client_api/README.md)**: Uses Message protocol for client operations

## Design Principles

This package exemplifies several key design principles:

- **Single Responsibility**: Defines only message representation, nothing else
- **Open/Closed**: Open for extension via implementations, closed for modification
- **Dependency Inversion**: High-level code depends on this abstraction, not concrete implementations
- **Interface Segregation**: Contains only essential message properties, no unnecessary methods