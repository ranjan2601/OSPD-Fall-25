# End-to-End (E2E) Tests

This directory contains end-to-end tests that verify the complete application workflow with **real external services** and **real credentials**.

## Overview

E2E tests differ from integration tests:
- **Integration Tests** (`tests/integration/`): Mock external APIs, test component interactions
- **E2E Tests** (`tests/e2e/`): Use real services, test complete user workflows

## Test Files

### 1. `test_gemini_e2e.py` (27 tests)
Tests the Gemini AI Chat Service with real Gemini API:
- ✅ Complete chat workflows
- ✅ Conversation history persistence
- ✅ Multi-user scenarios
- ✅ Concurrent access
- ✅ Special character handling
- ✅ Error recovery
- ✅ Authorization enforcement

**Requirements:**
- Service running at `http://127.0.0.1:8000`
- `GEMINI_API_KEY` environment variable set

**Run with:**
```bash
# Start the service
uv run uvicorn gemini_service.main:app --reload

# In another terminal, run tests
export GEMINI_API_KEY=your_api_key_here
uv run pytest tests/e2e/test_gemini_e2e.py -v
```

### 2. `test_orchestrator_e2e.py` (18 tests)
Tests the AI Chat Orchestrator Service with real Gemini, Jira, and Google Tasks APIs:

#### Core Orchestrator Tests (6 tests)
- ✅ Service health check
- ✅ Discord message processing with AI
- ✅ Discord conversation context
- ✅ Discord metrics tracking
- ✅ Slack message processing with AI
- ✅ Slack metrics tracking

**Requirements:**
- Service running at `http://127.0.0.1:8080`
- `GEMINI_API_KEY` environment variable set

#### Jira Integration Tests (3 tests) - `@pytest.mark.local_credentials`
- ✅ List Jira tickets
- ✅ Create and retrieve Jira ticket
- ✅ Search tickets with query

**Additional Requirements:**
- Jira OAuth credentials configured
- Jira API access enabled

#### Google Tasks Integration Tests (2 tests) - `@pytest.mark.local_credentials`
- ✅ List Google Tasks
- ✅ Create and retrieve task

**Additional Requirements:**
- Google Tasks OAuth credentials configured
- Google Tasks API access enabled

#### Full Workflow Tests (3 tests) - `@pytest.mark.local_credentials`
- ✅ Discord → AI → Jira → Response
- ✅ Slack → AI → Google Tasks → Response
- ✅ Conversation context with tickets

#### Stress Tests (2 tests)
- ✅ Multiple sequential requests
- ✅ Service stability across channels

**Run with:**
```bash
# Start the service
uv run uvicorn orchestrator_service.api:app --port 8080 --reload

# In another terminal, run tests

# Run only core tests (without credentials)
export GEMINI_API_KEY=your_api_key_here
uv run pytest tests/e2e/test_orchestrator_e2e.py -v -m "e2e and not local_credentials"

# Run all tests including credential-based tests
export GEMINI_API_KEY=your_api_key_here
# Configure Jira and Google Tasks credentials in your environment
uv run pytest tests/e2e/test_orchestrator_e2e.py -v
```

## Test Markers

We use pytest markers to categorize E2E tests:

- `@pytest.mark.e2e` - All E2E tests (requires services running)
- `@pytest.mark.local_credentials` - Requires local OAuth credentials (Jira, Google Tasks)

## Running E2E Tests

### Local Development

#### 1. Run Core E2E Tests (No credentials needed)
```bash
# Set API key
export GEMINI_API_KEY=your_api_key_here

# Start services in separate terminals
uv run uvicorn gemini_service.main:app --reload
uv run uvicorn orchestrator_service.api:app --port 8080 --reload

# Run core E2E tests
uv run pytest tests/e2e/ -v -m "e2e and not local_credentials"
```

#### 2. Run All E2E Tests (With credentials)
```bash
# Set API key
export GEMINI_API_KEY=your_api_key_here

# Configure OAuth credentials
# - Jira: Set JIRA_CLIENT_ID, JIRA_CLIENT_SECRET, JIRA_CLOUD_ID
# - Google Tasks: Run authentication flow to generate token.json

# Start services
uv run uvicorn gemini_service.main:app --reload
uv run uvicorn orchestrator_service.api:app --port 8080 --reload

# Run all E2E tests
uv run pytest tests/e2e/ -v -m e2e
```

### CI/CD Pipeline (CircleCI)

E2E tests with credentials run in CircleCI using the `gmail-client` context:

```yaml
# .circleci/config.yml
integration_test:
  steps:
    - checkout
    - run: uv sync
    - run:
        name: Run Live Integration Tests
        command: |
          uv run pytest tests/e2e/ tests/integration/ \
            -m "e2e or local_credentials" \
            --cov=src \
            --cov-report=term-missing
  context:
    - gmail-client  # Provides GEMINI_API_KEY, Google OAuth credentials
```

**CircleCI Context Variables:**
- `GEMINI_API_KEY` - Gemini API key for AI functionality
- Google Tasks OAuth credentials (token.json equivalent)
- Jira OAuth credentials (if applicable)

## Test Isolation

E2E tests ensure isolation:

1. **Unique Identifiers**: Each test generates unique channel IDs, user IDs, and message content
   ```python
   unique_channel_id = f"e2e_channel_{uuid.uuid4().hex[:8]}"
   ```

2. **Independent Channels**: Different tests use different channels to avoid interference

3. **Cleanup**: Tests that create tickets/tasks should clean up after themselves (future improvement)

## What E2E Tests Verify

### Complete User Workflows ✅
- User sends message → AI processes → System responds
- User asks about tickets → AI fetches → System returns formatted data
- User continues conversation → AI maintains context → System responds appropriately

### Real Service Integration ✅
- Real Gemini API calls (not mocked)
- Real Jira API calls (when configured)
- Real Google Tasks API calls (when configured)
- Real database operations
- Real HTTP endpoints

### System Reliability ✅
- Service stability under load
- Error recovery and graceful degradation
- Concurrent user access
- Metrics accuracy
- Authorization enforcement

## Troubleshooting

### "Service not running" Error
```
pytest.skip: Service not running at http://127.0.0.1:8080
```
**Solution:** Start the service first:
```bash
uv run uvicorn orchestrator_service.api:app --port 8080 --reload
```

### "GEMINI_API_KEY not set" Error
```
pytest.skip: GEMINI_API_KEY not set in environment
```
**Solution:** Export your API key:
```bash
export GEMINI_API_KEY=your_api_key_here
```

### "Jira not configured" or "Google Tasks not configured"
These tests are skipped automatically if credentials aren't configured. This is expected behavior for local development.

### Connection Timeout
If tests timeout, verify:
1. Service is running and healthy: `curl http://127.0.0.1:8080/health`
2. API key is valid
3. Network connection is stable

## Best Practices

### Writing New E2E Tests

1. **Use fixtures for setup:**
   ```python
   def test_my_workflow(
       check_service_running: Any,
       check_gemini_api_key: Any,
       http_client: httpx.Client,
       unique_channel_id: str,
   ) -> None:
       # Test code here
   ```

2. **Test complete workflows, not individual functions:**
   ```python
   # Good: Tests full flow
   def test_user_asks_for_tickets_and_receives_response():
       response = http_client.post("/discord/process", json={"message": "Show tickets"})
       assert "ticket" in response.json()["response"].lower()

   # Bad: Tests implementation details
   def test_orchestrator_parse_ticket_command():
       # This belongs in integration tests
   ```

3. **Skip gracefully when dependencies unavailable:**
   ```python
   if response.status_code >= 500:
       pytest.skip("Jira not configured for this environment")
   ```

4. **Use markers appropriately:**
   - `@pytest.mark.e2e` - All E2E tests
   - `@pytest.mark.local_credentials` - Tests requiring OAuth credentials

5. **Ensure test isolation:**
   - Use unique IDs for each test
   - Don't rely on specific data existing
   - Clean up created resources (future improvement)

## Coverage

E2E tests complement unit and integration tests:

| Test Type | What It Covers | Mocking | Speed |
|-----------|---------------|---------|-------|
| Unit Tests | Individual functions/classes | Heavy | Fast |
| Integration Tests | Component interactions | Moderate | Medium |
| **E2E Tests** | **Complete workflows** | **None** | **Slow** |

**Coverage Strategy:**
- Unit tests: 80%+ coverage of all code
- Integration tests: Verify component interactions with mocked external services
- **E2E tests: Verify complete user workflows with real services**

## CI/CD Integration

### Test Stages in CircleCI

1. **`unit_test` job** (All branches, all PRs)
   - Runs: `uv run pytest src/ --cov=src --cov-fail-under=85`
   - Purpose: Fast feedback on code changes
   - Coverage: 85% minimum

2. **`circleci_test` job** (All branches, all PRs)
   - Runs: `uv run pytest src/ tests/ -m "not local_credentials"`
   - Purpose: Unit + integration tests without credentials
   - Coverage: 80% minimum

3. **`integration_test` job** (main/develop only, with credentials)
   - Runs: `uv run pytest tests/e2e/ tests/integration/ -m "e2e or local_credentials"`
   - Purpose: Full E2E tests with real services and credentials
   - Context: `gmail-client` (provides API keys and OAuth tokens)

### When E2E Tests Run

- **On every commit:** Core E2E tests (without credentials)
- **On main/develop:** Full E2E tests (with credentials from CircleCI context)
- **Locally:** Developer can run with their own credentials

## Summary

E2E tests verify that the **complete system works end-to-end** with real services:
- ✅ 45+ E2E tests covering Gemini and Orchestrator services
- ✅ Real API integration (Gemini, Jira, Google Tasks)
- ✅ Complete user workflows (Input → AI → Tickets → Output)
- ✅ Runs in CI/CD with CircleCI context for credentials
- ✅ Graceful degradation when optional services unavailable
- ✅ Test isolation with unique identifiers
- ✅ Comprehensive coverage of service reliability and stability
