# Mail Client Service

A FastAPI service that exposes mail client functionality over HTTP REST API.

## Overview

This package contains the FastAPI application that wraps the `gmail_client_impl` component and exposes its functionality via RESTful HTTP endpoints. This is a **service** - it runs independently and is accessed over the network.

## Architecture

The service is a thin wrapper around existing components:
- Uses `mail_client_api.get_client()` to obtain a mail client instance
- Uses `gmail_client_impl` for the actual Gmail API integration
- Exposes REST endpoints for remote access

## Dependencies

- `fastapi` - Web framework for building APIs
- `uvicorn` - ASGI server for running FastAPI
- `mail-client-api` - Protocol definition (workspace dependency)
- `gmail-client-impl` - Gmail client implementation (workspace dependency)

## API Endpoints

### GET /
Health check endpoint.

**Response:**
```json
{
  "message": "Mail Client Service is running"
}
```

### GET /messages
Fetches a list of message summaries.

**Response:**
```json
{
  "messages": [
    {
      "id": "msg123",
      "subject": "Hello",
      "sender": "user@example.com",
      "body": "Message body..."
    }
  ]
}
```

### GET /messages/{message_id}
Fetches the full detail of a single message.

**Response:**
```json
{
  "message": {
    "id": "msg123",
    "subject": "Hello",
    "sender": "user@example.com",
    "body": "Message body..."
  }
}
```

### POST /messages/{message_id}/mark-as-read
Marks a message as read.

**Response:**
```json
{
  "message_id": "msg123",
  "status": "Marked as read"
}
```

### DELETE /messages/{message_id}
Deletes a message.

**Response:**
```json
{
  "message_id": "msg123",
  "status": "Deleted"
}
```

## Running the Service

```bash
# Start the service
uvicorn mail_client_service.main:app --reload

# Or using uv
uv run uvicorn mail_client_service.main:app --reload
```

The service will be available at `http://localhost:8000`.

Visit `http://localhost:8000/docs` for interactive API documentation.

## Testing

Run the service tests:

```bash
pytest src/mail_client_service/tests/
```

## Mock Client Fallback

If Gmail credentials are not available, the service automatically falls back to a MockClient that returns test data. This allows the service to run in CI/CD environments without real credentials.

## Notes

- This is a **service**, not a library. It should not be imported directly in application code.
- The service owns its own process and memory space.
- Authentication credentials (`credentials.json` or `token.json`) must be available for the service to access real Gmail data.
- For client-side usage, see the `mail_client_adapter` package instead.
