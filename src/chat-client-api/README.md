# Chat Client API

Abstract contract for chat client implementations.

## Overview

This package defines the abstract interfaces for chat services (Discord, Slack, Teams, etc.).
It provides base classes and factory functions that any chat implementation must conform to.

## Key Abstractions

- **Client**: Main interface for chat operations (send, retrieve, delete messages)
- **Message**: Represents a single chat message with metadata
- **Channel**: Represents a chat channel or conversation

## Usage

```python
import chat_client_api

# Get a client instance (implementation injected at runtime)
client = chat_client_api.get_client(user_id="user123")

# Send a message
message = client.send_message(channel_id="12345", content="Hello, world!")

# Get recent messages
messages = list(client.get_messages(channel_id="12345", max_results=10))

# List channels
channels = list(client.get_channels())
```

## Design Pattern

This package uses the **Factory Pattern** with **Dependency Injection**:

1. Implementations (e.g., `discord_client_impl`) override the factory functions
2. The registration happens at import time via side-effect imports
3. User code depends only on the abstract interface, not concrete implementations

## Type Safety

This package is fully typed with `py.typed` marker for mypy compatibility.
