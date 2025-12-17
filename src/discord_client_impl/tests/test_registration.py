"""Unit tests for Discord client implementation."""

from discord_client_impl import get_client_impl


def test_get_client_impl_returns_discord_client() -> None:
    """Test that get_client_impl returns a DiscordClient instance."""

    client = get_client_impl(user_id="test_user")

    assert client is not None
    # Verify it has DiscordClient methods
    assert hasattr(client, "_get_authorization_url")
    assert hasattr(client, "_exchange_code_for_token")
