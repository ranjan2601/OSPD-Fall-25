# Integration Tests - Mocking Strategy

## Overview

This directory contains integration tests that verify interactions between multiple components of the AI-Chat-Orchestrator system. These tests follow a careful mocking strategy to avoid expensive API calls while still testing realistic component interactions.

## Mocking Strategy

### What We Mock

1. **External AI APIs (Gemini)**
   - **Why**: Expensive, rate-limited, and non-deterministic
   - **How**: Mock `ai_client.generate_response()` to return predictable responses
   - **Example**: `mock_ai.generate_response.return_value = "JIRA:GET_TICKETS:limit=5"`

2. **External Chat APIs (Slack, Discord)**
   - **Why**: Requires authentication, may have side effects (real messages sent)
   - **How**: Mock `chat_client.get_messages()` and `chat_client.send_message()`
   - **Example**: See `test_ai_slack_integration.py`

3. **External Ticket APIs (Jira, Google Tasks)**
   - **Why**: Expensive API calls, requires authentication, modifies real tickets
   - **How**: Mock `ticket_client.search_tickets()`, `get_ticket()`, etc.
   - **Example**: See `test_ai_ticket_full_workflow.py`

### What We DON'T Mock

1. **Orchestrator Logic** - Real `AIChatOrchestrator` class is used
2. **Component Interactions** - Real method calls between components
3. **Data Transformations** - Real parsing, formatting, error handling
4. **Metrics Tracking** - Real metrics calculation and aggregation
5. **Conversation History** - Real history management

### Integration Test Categories

#### 1. Component Interaction Tests (8 pts)
Tests that verify two specific components work together:

- **AI + Chat**: `test_ai_slack_integration.py`, `test_ai_discord_integration.py`
  - Verifies AI interprets user messages from chat platforms
  - Tests AI responses are formatted correctly for chat platforms

- **AI + Tickets**: `test_ai_ticket_full_workflow.py`
  - Verifies AI interprets ticket commands correctly
  - Tests ticket data is formatted for user consumption
  - Validates switching between Jira and Google Tasks

- **Orchestrator Integration**: `test_orchestrator_full_workflow.py`
  - Tests complete workflows through the orchestrator
  - Verifies metrics tracking across workflows
  - Tests error handling between components

#### 2. End-to-End (E2E) Tests (8 pts)
Located in `tests/e2e/test_gemini_e2e.py`:

- **Real Service Deployment**: Tests run against localhost:8000
- **Real API Credentials**: Uses `GEMINI_API_KEY` from environment
- **Complete User Flow**: Input → Processing → Storage → Output
- **Markers**: All E2E tests marked with `@pytest.mark.e2e`
- **CI Integration**: Runs in CircleCI with secrets from context

**Example E2E Test**:
```python
@pytest.mark.e2e
def test_gemini_complete_chat_workflow(check_service_running, check_gemini_api_key):
    # Test sends real HTTP request to service
    # Service uses real Gemini API
    # Verifies complete workflow end-to-end
```

#### 3. Mocking Strategy Documentation (5 pts)
This document explains:

- ✅ Which external APIs are mocked (AI, Chat, Tickets)
- ✅ Why they are mocked (expensive, rate-limited, side effects)
- ✅ How to run integration tests with mocks
- ✅ How to designate "live" integration tests (use `@pytest.mark.e2e`)

### Live Integration Tests

Some tests are designated as "live" and hit real APIs:

1. **Marker**: Use `@pytest.mark.e2e` for tests that need real APIs
2. **Skip Condition**: Tests skip if credentials not available
3. **CI Only**: Typically run only in CI with proper secrets configured

**Example**:
```python
@pytest.mark.e2e
def test_with_real_gemini_api():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")
    # Test uses real API...
```

## Running Integration Tests

### Run All Integration Tests (Mocked)
```bash
pytest tests/integration/ -v
```

### Run E2E Tests (Real APIs)
```bash
# Requires service running and API keys set
pytest tests/e2e/ -v
```

### Run in CI
```bash
# CircleCI runs both integration and E2E tests
pytest src/ tests/ -m "not local_credentials" --cov=src
```

### Skip E2E Tests Locally
```bash
pytest tests/integration/ -v -m "not e2e"
```

## Test Structure

### Integration Test Pattern
```python
@pytest.mark.integration
def test_component_a_with_component_b():
    # 1. Setup real components
    component_a = RealComponentA()

    # 2. Mock external dependencies
    mock_external = Mock()
    mock_external.api_call.return_value = "mocked data"

    # 3. Test interaction
    result = component_a.process(mock_external)

    # 4. Verify both components involved
    assert component_a.method_was_called
    assert mock_external.api_call.called
```

### E2E Test Pattern
```python
@pytest.mark.e2e
def test_complete_workflow():
    # 1. Check prerequisites (service running, credentials available)
    if not service_running():
        pytest.skip("Service not running")

    # 2. Make real HTTP request
    response = httpx.post(SERVICE_URL, json=request_data)

    # 3. Verify complete workflow
    assert response.status_code == 200
    assert response.json()["result"]  # Real AI response
```

## CI Pipeline Integration (4 pts)

CircleCI configuration (`.circleci/config.yml`) includes:

### Job: `circleci_test`
- Runs **all tests** except those requiring local credentials
- Includes both unit and integration tests
- Uses mocks for expensive APIs
- Command: `pytest src/ tests/ -m "not local_credentials"`

### Job: `integration_test`
- Runs **live integration tests** with real credentials
- Only on `main`/`develop` branches
- Uses `gmail-client` context for secrets
- Command: `pytest -m "integration and not local_credentials"`

### Workflow: `build_and_test`
- Runs on all branches
- Executes: `build` → `lint` → `unit_test` → `circleci_test`

### Workflow: `full_integration`
- Runs on `main`/`develop` only
- Executes: `build` → `lint` → `unit_test` → `circleci_test` → `integration_test`
- **`integration_test` job uses real API credentials from CircleCI context**

## Metrics

- **Total Integration Tests**: 25+
- **Component Interaction Tests**: 15+
- **E2E Tests**: 10+
- **Coverage**: Integration tests don't count towards code coverage (they test interactions, not lines)

## Adding New Integration Tests

1. **Identify Components**: Which 2+ components are you testing?
2. **Mock External APIs**: Mock expensive/side-effect APIs
3. **Use Real Components**: Don't mock the components being tested
4. **Add Marker**: Use `@pytest.mark.integration`
5. **Document**: Add to this README if introducing new patterns

## Troubleshooting

### Test Fails with "Service not running"
- E2E tests require service at localhost:8000
- Start with: `uv run uvicorn gemini_service.main:app --reload`

### Test Skips with "API key not set"
- E2E tests require `GEMINI_API_KEY` environment variable
- Set with: `export GEMINI_API_KEY=your_key`

### Mock Not Working
- Ensure you're patching at the right location (where it's used, not defined)
- Use `patch.object()` for instance methods
- Check import order
