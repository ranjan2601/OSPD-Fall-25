# AI Chat Orchestrator

The AI Chat Orchestrator coordinates message flow between chat platforms (Discord, Slack) and AI services, with optional integration for ticketing systems (Jira, Google Tasks).

## Overview

This package provides the core orchestration logic that:

- Receives messages from chat platforms
- Processes them through AI services
- Handles ticket/task management commands
- Maintains conversation history per channel
- Tracks telemetry metrics for monitoring

## Architecture

The orchestrator follows a dependency injection pattern where AI clients, chat clients, and ticket clients are injected at initialization. This allows for easy swapping of implementations without changing the orchestration logic.

### Key Components

- **AIChatOrchestrator**: Main orchestration class that coordinates all services
- **Factory Functions**: Helper functions to create pre-configured orchestrator instances
- **SlackChatClient**: Slack-specific chat client implementation

## Usage

### Creating an Orchestrator

```python
from ai_chat_orchestrator import create_gemini_discord_orchestrator

orchestrator = create_gemini_discord_orchestrator(
    gemini_api_key="your-api-key",
    system_prompt="You are a helpful assistant"
)
```

### Processing Messages

```python
# Process a message directly
response = orchestrator.process_direct(
    channel_id="channel-123",
    user_input="What are my open tickets?"
)

# Handle a message from chat platform
success = orchestrator.handle_message(
    channel_id="channel-123",
    message_id="msg-456"
)
```

### Telemetry

```python
# Get metrics
metrics = orchestrator.get_metrics()
print(f"Success rate: {metrics['success_rate']}")
print(f"Average latency: {metrics['average_latency_seconds']}s")
```

## Features

### Conversation History

The orchestrator maintains conversation history per channel, limited to the last 10 exchanges. This enables context-aware responses from the AI.

### Ticket Integration

When configured with ticket clients (Jira or Google Tasks), the orchestrator can:

- Fetch tickets with status filtering
- Search tickets by query
- Retrieve specific tickets by ID
- Format ticket data for chat display

The AI can invoke ticket commands using special syntax:
- `JIRA:GET_TICKETS:limit=5` - Get recent Jira tickets
- `GTASKS:SEARCH_TICKETS:status=open` - Search Google Tasks by status
- `JIRA:GET_TICKET:id=ABC-123` - Get specific Jira ticket

### Metrics Tracking

The orchestrator tracks:
- Total requests processed
- Success/failure rates
- AI generation time
- Chat send time
- Total latency

## Dependencies

- `ai_client_api`: Abstract AI client interface
- `chat_client_api`: Abstract chat client interface
- `tickets_api`: Ticket status enums and types
- `slack_impl`: Slack API client (for Slack integration)

## Testing

Run tests with pytest:

```bash
pytest src/ai_chat_orchestrator/tests/
```

## Configuration

The orchestrator accepts several configuration options:

- **system_prompt**: Instructions for the AI model
- **ticket_client**: Optional legacy ticket client
- **jira_client**: Optional Jira-specific client
- **gtasks_client**: Optional Google Tasks client

When ticket clients are provided, the system prompt is automatically enhanced with ticket command syntax.
