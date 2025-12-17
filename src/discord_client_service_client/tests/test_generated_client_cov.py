"""Coverage tests for the auto-generated Discord service client.

We keep these tests minimal: hit request building + response parsing paths.
"""

import httpx
import respx

from discord_client_service_client import Client
from discord_client_service_client.api.default import (
    delete_message_guild_id_channels_channel_id_messages_message_id_delete,
    get_channel_guild_id_channels_channel_id_get,
    get_channels_guilds_guild_id_channels_get,
    get_messages_guild_id_channels_channel_id_messages_get,
    send_message_guild_id_channels_channel_id_messages_post,
)
from discord_client_service_client.models.send_message_request import SendMessageRequest


@respx.mock
def test_generated_client_basic_flows() -> None:
    base = "http://discord-svc"
    c = Client(base_url=base)

    # Exercise client helpers
    c = c.with_headers({"X-Test": "1"}).with_cookies({"session_id": "s"}).with_timeout(httpx.Timeout(2.0))

    guild_id = "g1"
    channel_id = "c1"
    message_id = "m1"

    respx.get(f"{base}/guilds/{guild_id}/channels").respond(
        200,
        json={"channels": [{"id": channel_id, "name": "general", "type": "text"}], "count": 1},
    )
    channels = get_channels_guilds_guild_id_channels_get.sync(client=c, guild_id=guild_id, session_id="s")
    assert channels is not None

    respx.get(f"{base}/{guild_id}/channels/{channel_id}").respond(
        200,
        json={"id": channel_id, "name": "general", "type": "text"},
    )
    ch = get_channel_guild_id_channels_channel_id_get.sync(client=c, guild_id=guild_id, channel_id=channel_id, session_id="s")
    assert ch is not None

    respx.get(
        f"{base}/{guild_id}/channels/{channel_id}/messages",
        params__contains={"limit": "1"},
    ).respond(
        200,
        json={
            "messages": [
                {
                    "id": message_id,
                    "channel_id": channel_id,
                    "content": "hi",
                    "sender_id": "u",
                    "sender_name": "n",
                    "timestamp": "t",
                }
            ],
            "count": 1,
        },
    )
    msgs = get_messages_guild_id_channels_channel_id_messages_get.sync(
        client=c, guild_id=guild_id, channel_id=channel_id, limit=1, session_id="s"
    )
    assert msgs is not None

    respx.post(f"{base}/{guild_id}/channels/{channel_id}/messages").respond(
        200,
        json={"status": "ok", "message": "sent"},
    )
    sent = send_message_guild_id_channels_channel_id_messages_post.sync(
        client=c,
        guild_id=guild_id,
        channel_id=channel_id,
        session_id="s",
        body=SendMessageRequest(content="hello"),
    )
    assert sent is not None

    respx.delete(f"{base}/{guild_id}/channels/{channel_id}/messages/{message_id}").respond(
        200,
        json={"status": "ok", "message": "deleted"},
    )
    deleted = delete_message_guild_id_channels_channel_id_messages_message_id_delete.sync(
        client=c,
        guild_id=guild_id,
        channel_id=channel_id,
        message_id=message_id,
        session_id="s",
    )
    assert deleted is not None


