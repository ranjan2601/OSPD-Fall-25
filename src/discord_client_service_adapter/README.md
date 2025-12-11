# Discord Client Service Adapter

This package provides an adapter that implements the `chat_client_api.Client` interface by wrapping the auto-generated OpenAPI client for the Discord service.

## Purpose

The adapter allows user code to interact with Discord through a remote HTTP service while using the same interface as the local `DiscordClient` implementation. This demonstrates the Adapter pattern and service-oriented architecture.

## Usage

```python
from discord_client_service_adapter import ServiceAdapterClient

# Create adapter pointing to a running service
# NOTE: this adapter no longer accepts `user_id`.
# You must provide an authenticated `session` and the `installed_guild_id`
# (the guild/server where the client/bot is installed) so the service can
# perform guild-scoped operations on behalf of the caller.
client = ServiceAdapterClient(
    service_url="http://localhost:8000",
    session="<session-token-or-session-object>",
    installed_guild_id="1234567890"
)

# Use the same interface as the local DiscordClient implementation
# (iterable/getters and send_message stay the same)
messages = list(client.get_messages(channel_id="123456", max_results=10))
client.send_message(channel_id="123456", content="Hello from adapter!")
```

## Architecture

```
User Code → ServiceAdapterClient → Generated HTTP Client → FastAPI Service → DiscordClient
```

The adapter translates between:
- The local `chat_client_api.Client` interface (Python objects, iterators)
- The remote HTTP API (JSON requests/responses, status codes)

Authentication and scoping:
- The adapter requires a `session` (an authenticated session token or session object) to be supplied when constructing `ServiceAdapterClient`. The session is used by the service to authenticate requests on behalf of the user or bot.
- Many Discord operations are guild-scoped for bots; the adapter therefore accepts `installed_guild_id` to indicate the guild (server) where the client/bot is installed. This ensures the service performs actions in the correct guild context.

## Dependencies

- `chat-client-api`: Defines the Client interface this adapter implements
- `discord-client-service-client`: Auto-generated HTTP client from OpenAPI spec
- `httpx`: HTTP client library used by the generated client
