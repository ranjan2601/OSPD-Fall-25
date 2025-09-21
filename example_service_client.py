#!/usr/bin/env python3
"""Example script demonstrating the auto-generated service client.

This script shows how the ServiceClient provides the same interface as the
Gmail client but communicates with a FastAPI service over HTTP.
"""

import mail_client_service_client
from mail_client_api import get_client


def main() -> None:
    """Demonstrate service client usage."""
    print("Service Client Example")
    print("======================")
    
    client = get_client(base_url="http://localhost:8000")
    
    print(f"Client type: {type(client)}")
    print(f"Base URL: {client._client.get_httpx_client().base_url}")
    
    try:
        print("\nFetching messages from service...")
        messages = list(client.get_messages(max_results=5))
        print(f"Retrieved {len(messages)} messages")
        
        for i, msg in enumerate(messages, 1):
            print(f"\nMessage {i}:")
            print(f"  ID: {msg.id}")
            print(f"  Subject: {msg.subject}")
            print(f"  From: {msg.from_}")
            print(f"  Date: {msg.date}")
            
        if messages:
            msg_id = messages[0].id
            print(f"\nMarking message {msg_id} as read...")
            success = client.mark_as_read(msg_id)
            print(f"Mark as read: {'Success' if success else 'Failed'}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the FastAPI service is running on http://localhost:8000")


if __name__ == "__main__":
    main()
