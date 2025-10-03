# FastAPI Mail Client Service

The `mail_client_service` package provides a RESTful API wrapper around the mail client functionality using FastAPI.

## Overview

This service exposes the mail client operations through HTTP endpoints, making it easy to interact with Gmail through a web API. The service automatically uses a mock client when no credentials are available, making it suitable for testing and development.

## API Endpoints

### Root Endpoint
```
GET /
```
Returns a simple health check message.

**Response:**
```json
{
  "message": "Mail Client Service is running"
}
```

### List Messages
```
GET /messages
```
Fetches a list of messages from the inbox.

**Query Parameters:**
- `max_results` (optional, default: 10) - Maximum number of messages to return

**Response:**
```json
{
  "messages": [
    {
      "id": "msg_123",
      "subject": "Test Email",
      "sender": "test@example.com",
      "body": "Email content..."
    }
  ]
}
```

### Get Single Message
```
GET /messages/{message_id}
```
Retrieves a specific message by ID.

**Path Parameters:**
- `message_id` - The ID of the message to retrieve

**Response:**
```json
{
  "message": {
    "id": "msg_123",
    "subject": "Test Email",
    "sender": "test@example.com",
    "body": "Email content..."
  }
}
```

### Delete Message
```
DELETE /messages/{message_id}
```
Deletes a specific message.

**Path Parameters:**
- `message_id` - The ID of the message to delete

**Response:**
```json
{
  "message_id": "msg_123",
  "status": "Deleted"
}
```

### Mark as Read
```
POST /messages/{message_id}/mark-as-read
```
Marks a message as read.

**Path Parameters:**
- `message_id` - The ID of the message to mark as read

**Response:**
```json
{
  "message_id": "msg_123",
  "status": "Marked as read"
}
```

## Running the Service

### Locally with uvicorn
```bash
uv run uvicorn src.mail_client_service.main:app --reload
```

The service will be available at `http://localhost:8000`

### With Docker
```bash
# Build the image
docker build -t mail-client-service .

# Run the container
docker run -d -p 8000:8000 --name mail-service mail-client-service

# Test the service
curl http://localhost:8000/
curl http://localhost:8000/messages
```

## Mock Client

When no Gmail credentials are available, the service automatically falls back to a built-in mock client that provides three test messages. This makes it easy to test and develop without requiring actual Gmail API access.

## ServiceClient

The `ServiceClient` class implements the `mail_client_api.Client` interface and communicates with the FastAPI service over HTTP. It uses the auto-generated client to make requests to the service endpoints.

**Key Methods:**
- `get_messages(max_results=10)` - Fetches a list of messages
- `get_message(message_id)` - Retrieves a specific message
- `delete_message(message_id)` - Deletes a message
- `mark_as_read(message_id)` - Marks a message as read

## ServiceMessage

The `ServiceMessage` class wraps the API response and provides the `mail_client_api.Message` interface. It exposes message properties like `id`, `subject`, `from_`, `to`, `date`, and `body`.

