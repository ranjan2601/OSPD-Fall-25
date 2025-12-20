# AI Chat Orchestrator

The AI Chat Orchestrator coordinates message flow between chat platforms (Discord, Slack) and AI services, with optional integration for ticketing systems (Jira, Google Tasks).

## Overview

This package provides the core orchestration logic that:

- Receives messages from chat platforms
- Processes them through AI services with natural language understanding
- Handles ticket/task management commands with priority support
- Supports title-based operations (update/close by title instead of UUID)
- Maintains conversation history per channel (last 10 exchanges)
- Extracts and displays priority from ticket descriptions
- Handles both UUID and string-based ticket IDs
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
- Create tickets with priority (LOW, MEDIUM, HIGH, CRITICAL)
- Update tickets by ID or title (case-insensitive partial matching)
- Close tickets by ID or title
- Retrieve specific tickets by ID
- Format ticket data for chat display with priority extraction

The AI can invoke ticket commands using special syntax:
- `JIRA:GET_TICKETS:limit=5` - Get recent Jira tickets
- `JIRA:CREATE_TICKET:title=Fix bug|description=Login broken|priority=HIGH` - Create with priority
- `JIRA:UPDATE_TICKET:title=Fix bug|status=IN_PROGRESS` - Update by title
- `JIRA:CLOSE_TICKET:id=ABC-123` - Close by ID
- `GTASKS:SEARCH_TICKETS:status=open` - Search Google Tasks by status
- `GTASKS:UPDATE_TICKET:title=Complete report|status=COMPLETED` - Update by title

### Priority Handling

Priority is extracted from ticket descriptions using the prefix pattern `[PRIORITY: VALUE]`:
- Adapter layer adds prefix when converting internal Jira tickets to shared interface
- Orchestrator extracts using regex and displays separately
- Supports LOW, MEDIUM, HIGH, CRITICAL values

### Title-Based Operations

Update and close operations support both ID and title:
- `id=UUID-or-string` - Direct ID lookup
- `title=Ticket Name` - Case-insensitive partial matching
- Returns first match if multiple tickets have similar titles
- Works with both Jira (UUIDs) and Google Tasks (string IDs)

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
- `tickets_api`: Ticket status enums and shared interface
- `ticket_api`: Adapter layer for internal to shared ticket conversion
- `slack_impl`: Slack API client (for Slack integration)

## Performance Characteristics

- **GTasks operations**: 1-2 seconds (fast authentication, simple API)
- **Jira operations**: 30-60 seconds (OAuth validation, user account lookups)
- **Conversation history**: In-memory per channel (cleared on restart)
- **Event deduplication**: 10-minute TTL for Slack webhook events

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
