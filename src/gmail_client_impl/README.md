# Gmail Client Implementation

## Overview

The `gmail_client_impl` package provides a concrete implementation of the **Client protocol** that connects to Gmail via the Google API. This package handles OAuth2 authentication, API communication, and integrates seamlessly with the Message protocol through the Gmail message implementation.

This implementation demonstrates the **"how"** of mail client operations, providing real connectivity to Gmail services while maintaining the clean interface defined by the Client protocol.

## Purpose

This package serves as the production-ready Gmail integration for the email assistant system:

- **Gmail API Integration**: Connects to Gmail using official Google APIs
- **OAuth2 Authentication**: Handles secure authentication with multiple modes (interactive/non-interactive)
- **Protocol Implementation**: Provides concrete implementation of all Client operations
- **Message Integration**: Works seamlessly with GmailMessage implementation
- **Dependency Injection**: Automatically registers itself as the Client implementation

## Architecture

### Implementation Strategy

The GmailClient class implements the Client protocol through:

1. **Authentication Management**: OAuth2 flow with credential handling for different environments
2. **API Communication**: Direct integration with Gmail API v1
3. **Message Processing**: Converts Gmail API responses to Message protocol objects
4. **Error Handling**: Robust error handling for network and API issues
5. **Environment Flexibility**: Supports both development and production authentication modes

### Authentication Modes

#### Interactive Mode (`interactive=True`)
- **Usage**: Development and first-time setup
- **Flow**: Opens browser for OAuth2 consent
- **Credentials**: Stores tokens locally for reuse
- **Requirements**: Access to browser and user interaction

#### Non-Interactive Mode (`interactive=False`)
- **Usage**: CI/CD, production servers, automated scripts
- **Flow**: Uses environment variables or pre-stored tokens
- **Credentials**: Reads from environment or credential files
- **Requirements**: Pre-configured authentication

### Dependency Injection

When this package is imported, it automatically overrides the `mail_client_api.get_client` factory function:

```python
import gmail_client_impl  # Automatically registers implementation

from mail_client_api import get_client
client = get_client()  # Returns a GmailClient instance
```

## API Reference

### GmailClient Class

```python
class GmailClient:
    """Gmail implementation of the Client protocol."""
    
    def __init__(self, interactive: bool = False):
        """Initialize Gmail client with authentication.
        
        Args:
            interactive: If True, may prompt for OAuth2 consent
                        If False, uses environment variables or stored tokens
        """
```

#### Methods (Client Protocol Implementation)

##### `get_message(message_id: str) -> Message`
Retrieve a specific Gmail message by ID.

**Implementation Details:**
- Calls Gmail API `messages().get()` with format='raw'
- Converts response to GmailMessage instance
- Handles API errors and rate limiting

**Usage:**
```python
message = client.get_message("gmail_msg_12345")
print(f"Subject: {message.subject}")
```

##### `delete_message(message_id: str) -> bool`
Delete a Gmail message permanently.

**Implementation Details:**
- Calls Gmail API `messages().delete()`
- Returns True on successful deletion
- Handles permission errors gracefully

**Usage:**
```python
if client.delete_message("spam_msg_123"):
    print("Spam message deleted")
```

##### `mark_as_read(message_id: str) -> bool`
Mark a Gmail message as read by removing the UNREAD label.

**Implementation Details:**
- Calls Gmail API `messages().modify()` to remove 'UNREAD' label
- Returns True on successful modification
- Handles cases where message is already read

**Usage:**
```python
if client.mark_as_read("important_msg_456"):
    print("Message marked as read")
```

##### `get_messages(max_results: int = 10) -> Iterator[Message]`
Retrieve multiple Gmail messages as an iterator.

**Implementation Details:**
- Calls Gmail API `messages().list()` for message IDs
- Fetches full message data for each ID in batches
- Yields GmailMessage instances as they're processed
- Implements efficient pagination

**Usage:**
```python
for message in client.get_messages(max_results=20):
    print(f"From: {message.from_} - Subject: {message.subject}")
```

### Factory Function

```python
def get_client_impl(interactive: bool = False) -> Client:
    """Create a GmailClient instance implementing the Client protocol.
    
    Args:
        interactive: Authentication mode flag
        
    Returns:
        Client: GmailClient instance conforming to Client protocol
    """
```

## Usage Examples

### Basic Operations

```python
import gmail_client_impl  # Register implementation
from mail_client_api import get_client

# Get client instance (non-interactive for production)
client = get_client(interactive=False)

# Retrieve recent messages
messages = client.get_messages(max_results=10)
for message in messages:
    print(f"ID: {message.id}")
    print(f"From: {message.from_}")
    print(f"Subject: {message.subject}")
    print(f"Date: {message.date}")
    print("---")
```

### Interactive Setup (Development)

```python
import gmail_client_impl
from mail_client_api import get_client

# Interactive mode for first-time setup
client = get_client(interactive=True)
# This will open browser for OAuth2 consent

# After authentication, normal operations work
messages = list(client.get_messages(max_results=5))
print(f"Retrieved {len(messages)} messages")
```

### Message Management

```python
import gmail_client_impl
from mail_client_api import get_client

client = get_client()

# Process and manage messages
for message in client.get_messages(max_results=50):
    # Mark promotional emails as read
    if "promotion" in message.subject.lower():
        client.mark_as_read(message.id)
        print(f"Marked promotion as read: {message.subject}")
    
    # Delete obvious spam
    if message.from_.endswith("suspicious-domain.com"):
        client.delete_message(message.id)
        print(f"Deleted spam from: {message.from_}")
```

### Error Handling

```python
import gmail_client_impl
from mail_client_api import get_client

try:
    client = get_client(interactive=False)
    
    # Attempt to get a message
    message = client.get_message("potentially_invalid_id")
    print(f"Retrieved: {message.subject}")
    
except Exception as e:
    print(f"Error accessing Gmail: {e}")
    # Handle authentication errors, network issues, etc.
```

## Authentication Setup

### Development Setup (Interactive)

1. **Google Cloud Console Setup**:
   - Create a project and enable Gmail API
   - Create OAuth2 credentials (Desktop application type)
   - Download `credentials.json`

2. **Local Development**:
   ```python
   import gmail_client_impl
   from mail_client_api import get_client
   
   # First run - opens browser for consent
   client = get_client(interactive=True)
   ```

3. **Token Storage**:
   - OAuth2 tokens are saved to `token.json`
   - Subsequent runs use stored tokens
   - Tokens auto-refresh when expired

### Production Setup (Non-Interactive)

1. **Environment Variables**:
   ```bash
   export GMAIL_CLIENT_ID="your_client_id"
   export GMAIL_CLIENT_SECRET="your_client_secret"
   export GMAIL_REFRESH_TOKEN="your_refresh_token"
   ```

2. **Production Usage**:
   ```python
   import gmail_client_impl
   from mail_client_api import get_client
   
   # Uses environment variables
   client = get_client(interactive=False)
   ```

3. **CI/CD Integration**:
   - Set environment variables in CircleCI/GitHub Actions
   - No browser interaction required
   - Tokens refresh automatically

### Credential Sources (Priority Order)

1. **Environment Variables** (highest priority)
   - `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`

2. **Local Token File**
   - `token.json` (created by interactive flow)

3. **Local Credentials File**
   - `credentials.json` (downloaded from Google Cloud Console)

## Testing

### Running Tests

```bash
# Run unit tests (with mocks, no real Gmail API calls)
uv run pytest src/gmail_client_impl/tests/ -v

# Run with coverage
uv run pytest src/gmail_client_impl/tests/ --cov=src/gmail_client_impl --cov-report=term-missing

# Run integration tests (requires authentication)
uv run pytest tests/integration/ -k gmail_client -v

# Run end-to-end tests (requires authentication)
uv run pytest tests/e2e/ -v
```

### Test Categories

#### Unit Tests (`src/gmail_client_impl/tests/`)
- **`test_authentication.py`**: Authentication flow testing with mocks
- **`test_core_methods.py`**: Core client methods with mocked Gmail API
- **`test_init.py`**: Client initialization and configuration

#### Integration Tests (`tests/integration/`)
- **Real API Testing**: Tests with actual Gmail API (marked `@pytest.mark.integration`)
- **Authentication Integration**: Verifies credential handling in different environments
- **Message Processing**: Tests complete flow from API to Message objects

#### End-to-End Tests (`tests/e2e/`)
- **Full Application Flow**: Complete user scenarios
- **Real Data Validation**: Verifies actual Gmail data handling

### Mock Testing

Unit tests use comprehensive mocking to avoid Gmail API calls:

```python
from unittest.mock import Mock, patch
from gmail_client_impl import GmailClient

@patch('gmail_client_impl._impl.build')
def test_get_messages(mock_build):
    # Mock Gmail API service
    mock_service = Mock()
    mock_build.return_value = mock_service
    
    # Mock API responses
    mock_service.users().messages().list().execute.return_value = {
        'messages': [{'id': 'msg_123'}]
    }
    
    client = GmailClient()
    messages = list(client.get_messages(max_results=1))
    assert len(messages) == 1
```

## Dependencies

### Required Dependencies

- **[mail_client_api](../mail_client_api/README.md)**: Client protocol for interface contract
- **[message](../message/README.md)**: Message protocol for return types
- **google-api-python-client**: Official Google API client library
- **google-auth-httplib2**: Authentication for Google APIs
- **google-auth-oauthlib**: OAuth2 flow handling

### Development Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Enhanced mocking capabilities
- **mypy**: Type checking

## Error Handling

### Authentication Errors

```python
try:
    client = get_client()
except Exception as auth_error:
    print(f"Authentication failed: {auth_error}")
    # Handle missing credentials, expired tokens, etc.
```

### API Errors

```python
try:
    message = client.get_message("invalid_id")
except Exception as api_error:
    print(f"Gmail API error: {api_error}")
    # Handle rate limiting, network issues, invalid message IDs
```

### Graceful Degradation

The client handles various error scenarios gracefully:

- **Rate Limiting**: Implements exponential backoff
- **Network Issues**: Retries with timeout handling
- **Invalid Message IDs**: Returns clear error messages
- **Permission Errors**: Provides helpful error context

## Performance Considerations

### Batch Operations

```python
# Efficient: Uses iterator for memory efficiency
for message in client.get_messages(max_results=100):
    process_message(message)

# Less efficient: Loads all messages into memory
messages = list(client.get_messages(max_results=100))
```

### Rate Limiting

The Gmail API has quotas and rate limits:

- **Daily Quota**: 1 billion API calls per day (generous)
- **Per-User Rate Limit**: 250 quota units per user per 100 seconds
- **Implementation**: Client handles rate limiting automatically

### Caching Strategy

- **Authentication Tokens**: Cached and auto-refreshed
- **Message Data**: Not cached (ensures fresh data)
- **API Connections**: Reused efficiently

## Related Components

- **[mail_client_api](../mail_client_api/README.md)**: Protocol interface implemented by this package
- **[gmail_message_impl](../gmail_message_impl/README.md)**: Used for creating Message objects from Gmail data
- **[message](../message/README.md)**: Protocol for Message return types

## Design Principles

This implementation follows key software engineering principles:

- **Single Responsibility**: Focuses solely on Gmail API integration
- **Open/Closed**: Extends the Client protocol without modifying it
- **Liskov Substitution**: Can be used anywhere a Client is expected
- **Dependency Inversion**: Implements the abstract Client protocol
- **Separation of Concerns**: API logic separated from protocol definition

## Gmail API Integration

### Scopes Required

The client requests these Gmail API scopes:

```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',  # Read messages
    'https://www.googleapis.com/auth/gmail.modify'     # Mark as read, delete
]
```

### API Endpoints Used

- **`messages().list()`**: Get message IDs from inbox
- **`messages().get()`**: Get full message data with raw content
- **`messages().modify()`**: Update message labels (mark as read)
- **`messages().delete()`**: Permanently delete messages

### Response Handling

Gmail API responses are processed efficiently:

1. **List Messages**: Gets paginated list of message IDs
2. **Batch Requests**: Fetches multiple message details efficiently
3. **Raw Content**: Retrieves base64url-encoded email data
4. **Message Creation**: Converts to GmailMessage instances through dependency injection