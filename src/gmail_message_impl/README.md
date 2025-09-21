# Gmail Message Implementation

## Overview

The `gmail_message_impl` package provides a concrete implementation of the **Message protocol** specifically designed for Gmail messages. This package handles the complex parsing and decoding of Gmail API message data into a clean, standardized interface.

This implementation demonstrates the **"how"** of message representation, taking raw Gmail API responses and transforming them into objects that conform to the Message protocol contract.

## Purpose

This package serves as the bridge between the Gmail API's data format and the application's Message protocol:

- **Data Parsing**: Converts Gmail API responses into Message protocol objects
- **Content Decoding**: Handles base64url decoding and email format parsing
- **Protocol Implementation**: Provides concrete implementation of all Message properties
- **Dependency Injection**: Automatically registers itself as the Message implementation

## Architecture

### Implementation Strategy

The GmailMessage class implements the Message protocol by:

1. **Raw Data Processing**: Parsing base64url-encoded email data from Gmail API
2. **Email Parsing**: Using Python's `email` library to extract headers and body
3. **Property Mapping**: Converting Gmail-specific fields to protocol properties
4. **Lazy Loading**: Parsing email content only when properties are accessed

### Dependency Injection

When this package is imported, it automatically overrides the `message.get_message` factory function:

```python
import gmail_message_impl  # Automatically registers implementation

from message import get_message
message = get_message(msg_id="123", raw_data="gmail_raw_data")
# Returns a GmailMessage instance
```

## API Reference

### GmailMessage Class

```python
class GmailMessage:
    """Concrete implementation of the Message protocol for Gmail messages."""
    
    def __init__(self, msg_id: str, raw_data: str):
        """Initialize a Gmail message from raw API data.
        
        Args:
            msg_id: Gmail message ID
            raw_data: Base64url-encoded raw email data from Gmail API
        """
```

#### Properties (Message Protocol Implementation)

All properties are computed from the parsed email data:

- **`id: str`** - Returns the Gmail message ID
- **`from_: str`** - Extracts sender from email headers
- **`to: str`** - Extracts recipient from email headers  
- **`date: str`** - Extracts date from email headers
- **`subject: str`** - Extracts subject from email headers
- **`body: str`** - Extracts plain text body content

### Factory Function

```python
def get_message_impl(msg_id: str, raw_data: str) -> Message:
    """Create a GmailMessage instance implementing the Message protocol.
    
    Args:
        msg_id: The Gmail message ID
        raw_data: Base64url-encoded raw email data from Gmail API
        
    Returns:
        Message: GmailMessage instance conforming to Message protocol
    """
```

## Usage Examples

### Direct Usage

```python
from gmail_message_impl import get_message_impl

# Create message from Gmail API data
message = get_message_impl(
    msg_id="gmail_msg_12345",
    raw_data="base64url_encoded_email_data..."
)

# Access message properties
print(f"Gmail ID: {message.id}")
print(f"From: {message.from_}")
print(f"Subject: {message.subject}")
print(f"Body: {message.body}")
```

### Protocol Usage (Recommended)

```python
import gmail_message_impl  # Register implementation
from message import get_message

# Use the protocol interface (implementation is injected)
message = get_message(
    msg_id="gmail_msg_12345", 
    raw_data="base64url_encoded_email_data..."
)

# Same interface, but now backed by Gmail implementation
print(f"Message type: {type(message)}")  # <class 'GmailMessage'>
print(f"Subject: {message.subject}")
```

### Integration with Gmail Client

```python
import gmail_message_impl  # Register message implementation
import gmail_client_impl   # Register client implementation

from mail_client_api import get_client

# Get client (Gmail implementation injected)
client = get_client()

# Get messages (automatically creates GmailMessage instances)
for message in client.get_messages(max_results=5):
    print(f"Gmail Message - Subject: {message.subject}")
    print(f"From: {message.from_}")
    print(f"Body preview: {message.body[:100]}...")
```

## Data Processing

### Gmail API Data Format

The Gmail API returns messages with base64url-encoded raw email data:

```json
{
    "id": "msg_12345",
    "raw": "base64url_encoded_email_content"
}
```

### Parsing Process

1. **Base64 Decoding**: Convert base64url string to bytes
2. **Email Parsing**: Use Python's `email.message_from_bytes()`
3. **Header Extraction**: Parse standard email headers (From, To, Subject, Date)
4. **Body Extraction**: Extract plain text content, handling multipart messages
5. **Property Caching**: Cache parsed values for performance

### Content Handling

The implementation handles various email formats:

- **Plain Text**: Direct extraction of text content
- **HTML**: Conversion to plain text or extraction of text parts
- **Multipart**: Navigation through message parts to find text content
- **Encoding**: Proper handling of various character encodings

## Error Handling

### Parsing Errors

```python
from gmail_message_impl import get_message_impl

try:
    message = get_message_impl("invalid_id", "invalid_data")
except ValueError as e:
    print(f"Invalid message data: {e}")
except Exception as e:
    print(f"Parsing error: {e}")
```

### Missing Headers

The implementation gracefully handles missing email headers:

```python
# If headers are missing, properties return appropriate defaults
message = get_message_impl("id", "minimal_email_data")

print(message.from_)    # May return "Unknown" or empty string
print(message.subject)  # May return "No Subject" or empty string
```

## Testing

### Running Tests

```bash
# Run unit tests for this component
uv run pytest src/gmail_message_impl/tests/ -v

# Run with coverage
uv run pytest src/gmail_message_impl/tests/ --cov=src/gmail_message_impl --cov-report=term-missing

# Run integration tests
uv run pytest tests/integration/ -k gmail_message -v
```

### Test Structure

- **Unit Tests**: Located in `tests/` directory
  - `test_gmail_message.py`: Core message parsing functionality
  - `test_edge_cases.py`: Error handling and edge cases
- **Integration Tests**: Located in `../../tests/integration/`
  - Test integration with Gmail client and protocol interfaces

### Mock Data

Tests use realistic Gmail API response data:

```python
SAMPLE_RAW_EMAIL = base64.urlsafe_b64encode(
    b"From: sender@example.com\r\n"
    b"To: recipient@example.com\r\n"
    b"Subject: Test Subject\r\n"
    b"Date: Mon, 1 Jan 2024 12:00:00 +0000\r\n"
    b"\r\n"
    b"Test email body content."
).decode()
```

## Dependencies

### Required Dependencies

- **[message](../message/README.md)**: Message protocol for interface contract
- **Python Standard Library**: 
  - `email`: For parsing email content
  - `base64`: For decoding Gmail raw data
  - `typing`: For type annotations

### Development Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **mypy**: Type checking

## Performance Considerations

### Lazy Loading

Properties are computed on-demand and cached:

```python
message = get_message_impl("id", "large_email_data")

# Email parsing happens only when properties are accessed
subject = message.subject  # Triggers parsing and caches result
subject_again = message.subject  # Returns cached value
```

### Memory Efficiency

- Raw data is stored as string, not bytes
- Parsed email object is created only once
- Properties are cached to avoid re-parsing
- Large attachments are not processed (focus on headers and text)

## Related Components

- **[message](../message/README.md)**: Protocol interface implemented by this package
- **[gmail_client_impl](../gmail_client_impl/README.md)**: Uses this implementation for message creation
- **[mail_client_api](../mail_client_api/README.md)**: Client interface that returns Message protocol objects

## Design Principles

This implementation follows key software engineering principles:

- **Single Responsibility**: Focuses solely on Gmail message parsing and protocol implementation
- **Open/Closed**: Extends the Message protocol without modifying it
- **Liskov Substitution**: Can be used anywhere a Message is expected
- **Dependency Inversion**: Implements the abstract Message protocol
- **Separation of Concerns**: Parsing logic separated from protocol definition

## Gmail-Specific Features

### Message ID Handling

Gmail message IDs are preserved as-is from the API:

```python
message = get_message_impl("1a2b3c4d5e6f", raw_data)
assert message.id == "1a2b3c4d5e6f"
```

### Date Format Handling

Gmail dates are normalized to a consistent string format:

```python
# Various Gmail date formats are handled
# "Mon, 1 Jan 2024 12:00:00 +0000"
# "1 Jan 2024 12:00:00 +0000" 
# All normalized to consistent output
```

### Character Encoding

The implementation handles various character encodings commonly found in emails:

- UTF-8 (most common)
- ISO-8859-1 (Latin-1)
- Windows-1252
- Other encodings as specified in email headers