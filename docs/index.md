# AI Chat Orchestrator Documentation

This project demonstrates a professional-grade microservices architecture for building AI-powered chat systems. The platform integrates Discord, Slack, Jira, and Google Tasks with AI capabilities through a component-based design emphasizing dependency injection and comprehensive testing.

## Live Deployment

**Service URL:** https://ai-chat-orchestrator-qvzc7dnvtq-uc.a.run.app

**API Documentation:** https://ai-chat-orchestrator-qvzc7dnvtq-uc.a.run.app/docs

## Quick Start

### Installation
```bash
# Install dependencies
uv sync --all-packages --extra dev

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
```

### Run the Orchestrator Service

```bash
# Set environment variables
export GEMINI_API_KEY="your_key"
export SLACK_BOT_TOKEN="your_token"  # Optional
export DISCORD_BOT_TOKEN="your_token"  # Optional

# Run the orchestrator service
uv run uvicorn orchestrator_service.api:app --port 8080 --reload

# Access API docs at http://localhost:8080/docs
```

### Run Tests
```bash
# Unit tests only
uv run pytest src/

# All CI-compatible tests
uv run pytest src/ tests/ -m "not local_credentials"

# With coverage report
uv run pytest src/ --cov --cov-report=html
```

## Architecture Layers

### AI Client Layer
1. **`ai_client_api`** - Abstract AIClient interface for AI service integration
2. **`gemini_client_impl`** - Google Gemini API implementation with structured output support
3. **`gemini_service`** - FastAPI service exposing Gemini capabilities via HTTP
4. **`gemini_adapter`** - HTTP adapter enabling microservices deployment

### Chat Client Layer
1. **`chat_client_api`** - Abstract ChatInterface for platform operations
2. **`discord_client_impl`** - Discord Gateway implementation with event handling
3. **`slack_impl`** - Slack Web API implementation with channel management

### Ticket Management Layer
1. **`ticket_api`** - Abstract ticket interface with priority support via description prefix
2. **`ticket_impl`** - Jira REST API implementation with OAuth 2.0 and user account lookup
3. **`gtasks_client_impl`** - Google Tasks API implementation with fast response times
4. **`tickets_api`** - Shared standardized interface for cross-system compatibility

### Orchestration Layer
1. **`ai_chat_orchestrator`** - Coordinates AI, chat, and ticket services
   - Natural language command processing
   - Title-based ticket operations with partial matching
   - Priority extraction and display
   - Conversation history management (last 10 exchanges per channel)
   - Polymorphic ID handling (UUID and string IDs)
2. **`orchestrator_service`** - Unified FastAPI service for all integrations
   - Discord and Slack message processing
   - Jira and Google Tasks CRUD operations
   - Slack webhook with event deduplication
   - Health checks and telemetry

## Key Features

### Natural Language Processing
- **Intelligent Command Routing** - AI automatically routes commands to Jira or Google Tasks
- **Priority Support** - Create tickets with LOW, MEDIUM, HIGH, or CRITICAL priority
- **Title-Based Operations** - Update and close tickets using natural titles instead of UUIDs
- **Conversation Context** - Maintains conversation history for coherent multi-turn interactions

### Multi-Platform Integration
- **Discord & Slack** - Full chat platform integration with message processing
- **Jira Integration** - Complete CRUD operations with OAuth 2.0 authentication
- **Google Tasks** - Fast task management (1-2s response time vs Jira's 30-60s)
- **Slack Webhooks** - Event-driven architecture with background processing

### Architecture & Quality
- **Component-Based Design** - Self-contained packages with clear interface boundaries
- **Dependency Injection** - Factory-based pattern enabling flexible component swapping
- **Type Safety** - Strict mypy checking across all modules
- **Comprehensive Testing** - 85%+ code coverage with unit, integration, and E2E tests
- **CI/CD Pipeline** - CircleCI with automated testing and deployment
- **Production Deployment** - GCP Cloud Run with Terraform infrastructure as code

### Performance Characteristics
- **GTasks Operations** - 1-2 second response time
- **Jira Operations** - 30-60 seconds (OAuth validation, user account lookup)
- **Event Deduplication** - Prevents duplicate Slack message processing
- **Telemetry Tracking** - Built-in metrics for success rates and latency

This documentation provides detailed information about the architecture, API contracts, testing strategies, and deployment guidelines.
