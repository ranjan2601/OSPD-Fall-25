# discord-client-service-client

A client library for accessing Discord Client Service

## Usage

First, create a client:

```python
from discord_client_service_client import Client

client = Client(base_url="http://localhost:8000")
```

Now call your endpoint and use your models:

```python
from discord_client_service_client.models import MessageDetail
from discord_client_service_client.api.default import get_messages_guild_id_channels_channel_id_messages_get
from discord_client_service_client.types import Response

response: Response[MessageListResponse] = get_messages_guild_id_channels_channel_id_messages_get.sync(
    guild_id="123456",
    channel_id="789012",
    client=client,
)
```

Or do the same thing with an async version:

```python
response: Response[MessageListResponse] = await get_messages_guild_id_channels_channel_id_messages_get.asyncio(
    guild_id="123456",
    channel_id="789012",
    client=client,
)
```

Things to know:
1. Every path/method combo has four functions:
    1. `sync`: Blocking request that returns parsed data (if successful) or `None`
    1. `sync_detailed`: Blocking request that always returns a `Request`, optionally with `parsed` set if the request was successful.
    1. `asyncio`: Like `sync` but async instead of blocking
    1. `asyncio_detailed`: Like `sync_detailed` but async instead of blocking

2. All path/query params and bodies become method arguments.
