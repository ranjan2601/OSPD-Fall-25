# Design Document: AI-Chat Orchestrator Platform

## Overview

This document describes the design and architecture of the AI-Chat Orchestrator platform, a professional-grade microservices system that integrates AI-powered chat capabilities with Discord, Slack, Jira, and Google Tasks. The platform demonstrates component-based design, dependency injection patterns, and service-oriented architecture at scale.

### System Components

The platform consists of multiple integrated layers:

1. **AI Client Layer** - Abstract AI interface with Gemini implementation and HTTP service
2. **Chat Client Layer** - Abstract chat interface with Discord and Slack implementations
3. **Ticket Management Layer** - Abstract ticket interface with Jira and Google Tasks implementations
4. **Orchestration Layer** - Coordinates AI, chat, and ticket services with conversation management, title-based operations, and priority handling
5. **Service Layer** - Unified FastAPI service exposing all functionality via REST API

### Problem Statement

Building a multi-platform chat integration system with AI capabilities presents several challenges:

- **Platform Diversity**: Discord, Slack, Jira, and Google Tasks have different APIs and authentication models
- **Tight Coupling**: Direct integration with each platform creates maintenance complexity
- **Testing Difficulty**: Testing requires credentials for multiple services
- **Scalability**: Need to support multiple concurrent users and conversations
- **State Management**: Conversation history must be maintained per channel/user
- **Error Resilience**: System must gracefully handle service failures
- **Priority Handling**: Shared ticket interface lacks priority field, requiring workaround
- **User Experience**: UUID-based operations difficult, need title-based alternatives
- **ID Compatibility**: Jira uses UUIDs, Google Tasks uses string IDs

**Solution**: Apply component-based architecture with clear interface boundaries, dependency injection for flexibility, orchestration layer for coordination, priority prefix workaround, title-based lookup with partial matching, and polymorphic ID handling.

---

## Architecture

### High-Level Design

```
┌────────────────────────────────────────────────────────────────────┐
│                    Client Applications                              │
│              (Discord Bot, Slack Bot, HTTP Clients)                 │
└───────────┬────────────────────────────────┬───────────────────────┘
            │                                │
            │ (Gateway/Events)               │ (HTTP API)
            │                                │
┌───────────▼──────────────┐     ┌──────────▼─────────────────────────┐
│   Chat Platform Bots     │     │   Orchestrator Service              │
│   (Discord.py, Slack)    │     │   (FastAPI REST API)                │
│                          │     │                                     │
│  - Event Handlers        │     │  - Process Message Endpoints        │
│  - Message Sending       │     │  - Channel Management               │
│  - Channel Management    │     │  - Ticket Management                │
└───────────┬──────────────┘     │  - Metrics & Health Checks          │
            │                    │  - Slack Webhook Handler            │
            │                    └──────────┬─────────────────────────┘
            │                               │
            └───────────────┬───────────────┘
                            │
                ┌───────────▼────────────────────────────────┐
                │   AI Chat Orchestrator                     │
                │   (Coordination Layer)                     │
                │                                            │
                │  - Message Processing                      │
                │  - Conversation History (per channel)      │
                │  - Ticket Command Routing (JIRA:/GTASKS:)  │
                │  - AI Response Formatting                  │
                │  - Telemetry Tracking                      │
                └────┬──────────┬──────────┬────────────────┘
                     │          │          │
        ┌────────────┘          │          └────────────────┐
        │                       │                           │
┌───────▼────────┐   ┌──────────▼────────┐   ┌────────────▼──────────┐
│  AI Clients    │   │  Chat Clients     │   │  Ticket Clients       │
│                │   │                   │   │                       │
│  - Gemini API  │   │  - Discord API    │   │  - Jira REST API      │
│  - Structured  │   │  - Slack Web API  │   │  - Google Tasks API   │
│    Output      │   │  - Channel Ops    │   │  - OAuth 2.0          │
└────────────────┘   └───────────────────┘   └───────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Abstract Interfaces   │
                    │                       │
                    │  - AIClient ABC       │
                    │  - ChatInterface ABC  │
                    │  - TicketInterface    │
                    └───────────────────────┘
```

### Design Principles Applied

1. **Interface-Implementation Separation**: All functionality defined by ABCs, implemented by concrete classes
2. **Dependency Injection**: Implementations injected at runtime via factory patterns
3. **Orchestration Pattern**: Central coordinator manages multi-service interactions
4. **Adapter Pattern**: Translates between incompatible interfaces (async/sync, different ticket systems)
5. **Singleton Pattern**: Global orchestrator instances for efficient resource usage
6. **Event-Driven Architecture**: Slack webhook uses background tasks for async processing

---

## Layer 1: AI Client Integration

### Purpose
Provide unified interface for AI operations across different providers, supporting both conversational and structured output modes.

### Components

**ai_client_api**: Abstract base class defining AI contract
- `generate_response()`: Main AI interaction method
- Supports text responses and JSON-structured output
- Optional system prompts and response schemas

**gemini_client_impl**: Google Gemini implementation
- Uses Gemini API for text generation
- Supports JSON schema-based structured output
- Configures response MIME type for structured mode

**gemini_service**: FastAPI service exposing Gemini via HTTP
- `/generate` endpoint for AI responses
- Health check endpoint
- Mock client fallback for testing

**gemini_adapter**: HTTP adapter implementing AIClient
- Delegates to gemini_service over HTTP
- Enables microservices deployment
- Uses auto-generated client

### Key Design Decisions

**1. Structured Output Support**
- **Decision**: Support optional JSON schema for structured responses
- **Rationale**:
  - Enables type-safe data extraction
  - AI can return structured ticket data, entities, etc.
  - More reliable than parsing natural language
- **Tradeoff**: More complex API surface

**2. Separation of Direct and Service Clients**
- **Decision**: Provide both direct API client and HTTP adapter
- **Rationale**:
  - Direct client for monolithic deployments
  - HTTP adapter for microservices architecture
  - Both implement same interface (transparent swap)
- **Tradeoff**: Must maintain two code paths

---

## Layer 2: Chat Client Integration

### Purpose
Standardize chat platform operations across Discord and Slack with unified interface.

### Components

**chat_client_api**: Abstract interface for chat operations
- `get_channels()`: List available channels
- `get_messages()`: Retrieve message history
- `send_message()`: Post messages to channels
- `delete_message()`: Remove messages

**discord_client_impl**: Discord Gateway implementation
- Uses discord.py for bot functionality
- Event-driven message handling
- Channel and message management

**slack_impl**: Slack Web API implementation
- HTTP-based Slack client
- Supports channel operations
- Message posting and retrieval

**slack_adapter**: Adapter for Slack HTTP operations
- Wraps Slack API client
- Implements ChatInterface
- Handles Slack-specific authentication

### Key Design Decisions

**1. Gateway vs REST for Discord**
- **Decision**: Use Discord Gateway (discord.py) instead of REST API
- **Rationale**:
  - Discord primarily uses Gateway for bots
  - Better event handling and real-time updates
  - discord.py abstracts complexity
- **Tradeoff**: NoOpChatClient needed (Gateway sends messages differently)

**2. NoOpChatClient Pattern**
- **Decision**: Create no-op implementation for Discord orchestrator
- **Rationale**:
  - Discord Gateway bot sends via discord.py, not ChatInterface
  - Orchestrator still needs ChatInterface for architecture consistency
  - NoOp satisfies type requirements without actual implementation
- **Tradeoff**: Slight architecture inconsistency

**3. Slack Event API Webhook**
- **Decision**: Support Slack webhook for event-driven architecture
- **Rationale**:
  - Enables real-time Slack message processing
  - More efficient than polling
  - Slack's recommended approach
- **Implementation**: Background tasks prevent timeout, event deduplication prevents retries

---

## Layer 3: Ticket Management Integration

### Purpose
Abstract ticket/task operations across Jira and Google Tasks with standardized interface.

### Components

**ticket_api**: Abstract interface for ticket operations
- `create_ticket()`: Create new tickets/tasks
- `get_ticket()`: Retrieve by ID
- `search_tickets()`: Query with filters
- `TicketStatus` enum: OPEN, IN_PROGRESS, CLOSED

**ticket_impl**: Jira REST API implementation
- OAuth 2.0 authentication
- Full CRUD operations
- Jira-specific field mapping

**gtask_client_impl**: Google Tasks implementation
- Google Tasks API integration
- OAuth 2.0 authentication
- Task lifecycle management

**StandardizedTicketAdapter**: Sync-to-sync adapter
- Normalizes different ticket interfaces
- Maps between Jira and common interface
- Handles status conversions

**AsyncStandardizedTicketAdapter**: Sync-to-async adapter
- Wraps sync ticket clients for FastAPI
- Runs blocking operations in thread pool
- Maintains async/await patterns

### Key Design Decisions

**1. Two Ticket Systems**
- **Decision**: Support both Jira and Google Tasks
- **Rationale**:
  - Different use cases (engineering vs personal tasks)
  - Demonstrates multi-provider architecture
  - Users can choose preferred system
- **Tradeoff**: More complexity in orchestration

**2. Adapter for Async Compatibility**
- **Decision**: Create AsyncStandardizedTicketAdapter for FastAPI
- **Rationale**:
  - FastAPI expects async methods
  - Ticket clients are synchronous
  - Thread pool execution prevents blocking
- **Tradeoff**: Extra adapter layer

**3. Status Enum Standardization**
- **Decision**: Common TicketStatus enum across providers
- **Rationale**:
  - Different systems use different status names
  - Need consistent interface for orchestrator
  - Enables cross-system queries
- **Tradeoff**: Loses provider-specific status granularity

**4. Priority Handling via Description Prefix**
- **Decision**: Prepend priority to description field as `[PRIORITY: VALUE]`
- **Rationale**:
  - Shared ticket interface lacks priority parameter
  - Adapter layer adds prefix when converting internal to shared tickets
  - Orchestrator extracts with regex and displays separately
  - Maintains backward compatibility
- **Tradeoff**: Not type-safe, relies on string parsing, couples adapter and orchestrator

---

## Layer 4: AI Chat Orchestrator

### Purpose
Coordinate message flow between chat platforms, AI services, and ticket systems while maintaining conversation state.

### Core Functionality

**Message Processing Flow:**
1. Receive message from chat platform or HTTP API
2. Retrieve conversation history for context
3. Send to AI with system prompt (including ticket commands if configured)
4. Parse AI response for ticket commands (JIRA:, GTASKS:)
5. Execute ticket commands if present (supports GET_TICKETS, SEARCH_TICKETS, CREATE_TICKET, UPDATE_TICKET, CLOSE_TICKET)
6. Handle title-based updates via case-insensitive partial matching
7. Extract and display priority from description prefix
8. Format response for chat platform
9. Send response and update conversation history
10. Track telemetry metrics

**Conversation History Management:**
- Maintains last 10 message exchanges per channel
- Provides context to AI for coherent responses
- Stored in-memory (cleared on restart)
- Per-channel isolation

**Ticket Command Routing:**
- AI responses can include special commands: `JIRA:GET_TICKETS:limit=5`
- Orchestrator parses command prefix (JIRA: or GTASKS:)
- Routes to appropriate ticket client
- Formats ticket data for chat display
- Returns formatted response instead of raw command

**System Prompt Enhancement:**
- Base system prompt provided at initialization
- If ticket clients configured, automatically appends command syntax documentation
- Instructs AI on when to use JIRA: vs GTASKS: prefixes
- Includes formatting rules for Slack/Discord

### Key Design Decisions

**1. In-Memory Conversation History**
- **Decision**: Store conversation history in orchestrator memory
- **Rationale**:
  - Fast access without database queries
  - Sufficient for demonstration and moderate scale
  - Stateful orchestrator instances
- **Tradeoff**: Lost on restart, not suitable for distributed deployment

**2. Command Prefix Routing**
- **Decision**: Use JIRA: and GTASKS: prefixes for routing
- **Rationale**:
  - AI can explicitly indicate which system to query
  - Simple string parsing for command detection
  - Clear in system prompt documentation
- **Tradeoff**: Couples AI responses to command format

**3. Singleton Orchestrator Instances**
- **Decision**: Maintain global orchestrator instances in service
- **Rationale**:
  - Conversation history persistence across requests
  - Efficient resource usage (one AI client, one chat client)
  - Simpler state management
- **Tradeoff**: Not horizontally scalable without shared state store

**6. Title-Based Ticket Operations**
- **Decision**: Support `title=` prefix in UPDATE_TICKET and CLOSE_TICKET commands
- **Rationale**:
  - UUIDs difficult for users to remember and type
  - Natural language references use titles
  - Case-insensitive partial matching provides flexibility
- **Implementation**: Search tickets by title match before ID lookup
- **Tradeoff**: Ambiguous if multiple tickets have similar titles (returns first match)

**7. Polymorphic ID Handling**
- **Decision**: Accept both UUID and string IDs in orchestrator
- **Rationale**:
  - Jira uses UUID format
  - Google Tasks uses arbitrary string IDs
  - Try UUID parsing first, fallback to string
- **Tradeoff**: Less type safety, potential for ID confusion across systems

**4. Automatic Formatting Cleanup**
- **Decision**: Remove markdown bold syntax from AI responses
- **Rationale**:
  - Slack/Discord render ** poorly
  - Gemini tends to use bold frequently
  - System prompt can guide formatting
- **Tradeoff**: Some formatting information lost

**5. Telemetry Tracking**
- **Decision**: Track metrics per orchestrator instance
- **Rationale**:
  - Monitor success rates and latency
  - Separate metrics for Discord vs Slack
  - Debugging and performance analysis
- **Metrics Tracked**: Total requests, success/failure counts, AI time, chat time, total latency

**8. Performance Characteristics**
- **Jira Latency**: 30-60 seconds per operation
  - OAuth token validation on each request
  - User account ID lookup for reporter/assignee
  - Jira Cloud API inherent latency
  - Potential optimization: cache user account IDs
- **Google Tasks Latency**: 1-2 seconds per operation
  - Simpler authentication model
  - No user account lookups
  - Faster API response times

---

## Layer 5: Orchestrator Service

### Purpose
Expose unified HTTP API for all platform integrations, enabling external access and centralized management.

### API Structure

**Discord Endpoints:**
- `POST /discord/process`: Process message with AI
- `GET /discord/channels`: List Discord channels
- `POST /discord/channels/{id}/messages`: Send message
- `GET /discord/metrics`: Telemetry

**Slack Endpoints:**
- `POST /slack/process`: Process message with AI
- `POST /webhook/slack`: Event API webhook
- `GET /slack/channels`: List Slack channels
- `POST /slack/channels/{id}/messages`: Send message
- `GET /slack/metrics`: Telemetry

**Jira Endpoints:**
- `POST /jira/tickets`: Create ticket
- `GET /jira/tickets/{id}`: Get ticket
- `GET /jira/tickets`: Search tickets

**Google Tasks Endpoints:**
- `POST /gtasks/tickets`: Create task
- `GET /gtasks/tickets/{id}`: Get task
- `GET /gtasks/tickets`: Search tasks

**System Endpoints:**
- `GET /health`: Health check
- `GET /`: Service status

### Slack Webhook Implementation

The Slack webhook endpoint demonstrates advanced event handling:

**URL Verification:**
- Handles Slack's challenge-response verification
- Returns challenge value immediately

**Event Deduplication:**
- Maintains cache of processed event IDs
- 10-minute TTL for cache entries
- Prevents duplicate processing from Slack retries

**Background Processing:**
- Returns 200 OK immediately to prevent Slack timeouts
- Processes message in background task
- Prevents Slack from retrying due to slow response

**Bot Loop Prevention:**
- Filters out messages from bots
- Prevents infinite response loops

### Key Design Decisions

**1. Background Task Processing**
- **Decision**: Use FastAPI BackgroundTasks for Slack message processing
- **Rationale**:
  - Slack requires 200 OK within 3 seconds
  - AI processing can take longer
  - Prevents timeout and retry storms
- **Tradeoff**: Can't return errors to Slack (always returns 200)

**2. Event Deduplication Cache**
- **Decision**: Maintain in-memory cache of processed event IDs
- **Rationale**:
  - Slack retries events if no 200 response
  - Processing same message twice creates duplicates
  - Simple dict with TTL cleanup
- **Tradeoff**: Lost on restart, doesn't work with multiple instances

**3. Singleton Factory Functions**
- **Decision**: Use global functions to create/retrieve orchestrators
- **Rationale**:
  - Ensures single instance per platform
  - Conversation history preserved across requests
  - Lazy initialization on first use
- **Tradeoff**: Global state, not thread-safe (but FastAPI handles this)

**4. Graceful Ticket Client Failures**
- **Decision**: Orchestrators work even if ticket clients unavailable
- **Rationale**:
  - Jira/Google Tasks are optional features
  - Service should work with just AI + chat
  - Log warnings but don't crash
- **Implementation**: Try/except in orchestrator creation, log warning, continue with None

**5. Separate Sync and Async Ticket Clients**
- **Decision**: Maintain both sync (for orchestrator) and async (for endpoints) Jira clients
- **Rationale**:
  - Orchestrator runs sync (called from Discord.py event loop)
  - FastAPI endpoints are async
  - Different threading models require different clients
- **Tradeoff**: Two client instances, potential consistency issues

---

## Testing Strategy

### Test Organization

**Unit Tests** (`src/*/tests/`):
- Mock all external dependencies
- Test individual components in isolation
- Fast execution (milliseconds)
- 85%+ coverage requirement

**Integration Tests** (`tests/integration/`):
- Test component interactions
- May use real APIs with test credentials
- Verify dependency injection works

**End-to-End Tests** (`tests/e2e/`):
- Full workflow tests with real services
- Marked with `@pytest.mark.e2e`
- Require all credentials

### Test Categories

```python
@pytest.mark.unit              # Fast, isolated
@pytest.mark.integration       # Component interactions
@pytest.mark.e2e              # Full workflows
@pytest.mark.circleci         # CI-compatible
@pytest.mark.local_credentials # Requires local files
```

### CI/CD Strategy

**All Branches:**
- Linting (Ruff)
- Type checking (MyPy)
- Unit tests with coverage
- Tests marked `circleci` (no credentials needed)

**Main/Develop Only:**
- Integration tests with environment variables
- E2E tests with CircleCI context credentials

### Mocking Strategy

**AI Client Mocking:**
- Mock client for CI (no API quota usage)
- Predefined responses for common queries
- Tests work without GEMINI_API_KEY

**Chat Client Mocking:**
- NoOpChatClient for Discord (messages sent via discord.py)
- Mock Slack responses in tests
- Verify message formatting without actual sending

**Ticket Client Mocking:**
- Mock Jira/Google Tasks in orchestrator tests
- Verify command parsing without API calls
- Test status conversions

---

## Deployment Architecture

### Local Development

```bash
# Install dependencies
uv sync --all-packages --extra dev

# Set environment variables
export GEMINI_API_KEY="your-key"
export SLACK_BOT_TOKEN="xoxb-token"
export DISCORD_BOT_TOKEN="discord-token"

# Run orchestrator service
uv run uvicorn orchestrator_service.api:app --port 8080 --reload
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen --all-packages

EXPOSE 8080
CMD ["uv", "run", "uvicorn", "orchestrator_service.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Cloud Deployment (GCP Cloud Run)

```bash
# Build for Cloud Run
docker build --platform linux/amd64 -t gcr.io/PROJECT/orchestrator .

# Push to GCR
docker push gcr.io/PROJECT/orchestrator

# Deploy with environment variables
gcloud run deploy orchestrator \
  --image gcr.io/PROJECT/orchestrator \
  --region us-central1 \
  --set-env-vars GEMINI_API_KEY=key,SLACK_BOT_TOKEN=token
```

### Infrastructure as Code (Terraform)

The `terraform/` directory contains infrastructure definitions:
- GCP Cloud Run service
- Secret management
- Networking configuration
- IAM permissions

---

## Design Tradeoffs Summary

### Architectural Strengths

1. **Interface-Based Design**: All components behind stable ABCs
2. **Multi-Platform Support**: Discord, Slack, Jira, Google Tasks
3. **Orchestration Pattern**: Clean coordination of multiple services
4. **Dependency Injection**: Flexible component swapping
5. **Comprehensive Testing**: 80%+ coverage with multiple test levels
6. **Event-Driven**: Slack webhook with background processing
7. **Telemetry**: Built-in metrics for monitoring

### Known Limitations

1. **In-Memory State**: Conversation history lost on restart
2. **Not Horizontally Scalable**: Singleton pattern prevents multi-instance
3. **Event Cache In-Memory**: Deduplication doesn't work across instances
4. **No Authentication**: Service endpoints unauthenticated
5. **Synchronous Orchestrator**: Can't handle high concurrency
6. **SQLite for Credentials**: Not suitable for production scale

### Production Improvements Needed

**For Production Deployment:**
1. **State Persistence**: Move conversation history to Redis/PostgreSQL
2. **Distributed State**: Share event cache across instances
3. **Authentication**: Add JWT/API key authentication to endpoints
4. **Async Orchestrator**: Rewrite orchestrator for async/await
5. **Database**: Replace SQLite with PostgreSQL
6. **Load Balancing**: Support horizontal scaling with shared state
7. **Monitoring**: Add Prometheus metrics, structured logging
8. **Rate Limiting**: Prevent API abuse
9. **Secrets Management**: Use proper secret management (GCP Secret Manager)

### What Worked Well

1. **Component Reusability**: Packages work independently
2. **Test Coverage**: Comprehensive testing without real credentials
3. **Mock Fallbacks**: CI/CD works without API keys
4. **Adapter Pattern**: Clean abstraction of sync/async differences
5. **OpenAPI Generation**: Auto-generated clients stay in sync
6. **Dependency Injection**: Clean testing with FastAPI overrides

---

## Conclusion

The AI-Chat Orchestrator platform successfully demonstrates professional-grade microservices architecture applied to a complex, multi-platform integration problem. The design emphasizes:

- **Separation of Concerns**: Clear boundaries between AI, chat, ticket, and orchestration layers
- **Interface Stability**: Abstract interfaces enable implementation swapping
- **Testability**: Comprehensive test coverage with multiple mock strategies
- **Extensibility**: New platforms easily added via interface implementation
- **Maintainability**: Component-based design simplifies evolution

The platform is production-ready with the documented limitations addressed. The architecture patterns demonstrated here (dependency injection, orchestration, adapter, factory) are applicable to any complex integration project.

---

## Future Enhancements

### Planned Features

1. **Additional AI Providers**: OpenAI, Claude integration via AIClient
2. **More Chat Platforms**: Teams, Telegram support
3. **Advanced Ticket Operations**: Updates, comments, attachments
4. **Conversation Threading**: Multi-turn conversations with context
5. **User Authentication**: Proper user identity management
6. **Analytics Dashboard**: Visualize usage metrics
7. **Custom AI Prompts**: Per-channel system prompts
8. **Webhooks for Jira**: Event-driven ticket updates

### Scalability Roadmap

1. **Phase 1**: Redis for conversation history
2. **Phase 2**: PostgreSQL for persistent data
3. **Phase 3**: Kubernetes deployment with multiple replicas
4. **Phase 4**: Message queue (RabbitMQ/Kafka) for event processing
5. **Phase 5**: Microservices split (AI service, Chat service, Ticket service)

The current monolithic architecture provides a solid foundation for gradual evolution to distributed microservices.
