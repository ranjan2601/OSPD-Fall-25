"""Factory functions for creating orchestrator instances."""

import logging

import chat_client_api

import ai_client_api
import discord_client_impl
import gemini_client_impl
from ai_chat_orchestrator.orchestrator import AIChatOrchestrator

logger = logging.getLogger(__name__)


def create_gemini_discord_orchestrator(
    gemini_api_key: str,
    discord_user_id: str | None = None,
    system_prompt: str = "You are a helpful AI assistant in a Discord channel.",
) -> AIChatOrchestrator:
    """Create orchestrator with Gemini AI and Discord chat.

    Args:
        gemini_api_key: API key for Gemini
        discord_user_id: Optional Discord user ID
        system_prompt: System instruction for AI

    Returns:
        Configured AIChatOrchestrator instance
    """
    gemini_client_impl.register()
    discord_client_impl.register()

    ai_client = ai_client_api.get_client(api_key=gemini_api_key)
    chat_client = chat_client_api.get_client(user_id=discord_user_id)

    return AIChatOrchestrator(
        ai_client=ai_client,
        chat_client=chat_client,
        system_prompt=system_prompt,
    )


def create_gemini_slack_orchestrator(
    gemini_api_key: str,
    slack_token: str,
    slack_base_url: str = "https://slack.com/api",
    system_prompt: str = "You are a helpful AI assistant in a Slack channel.",
) -> AIChatOrchestrator:
    """Create orchestrator with Gemini AI and Slack chat.

    Args:
        gemini_api_key: API key for Gemini
        slack_token: Slack OAuth token
        slack_base_url: Slack API base URL
        system_prompt: System instruction for AI

    Returns:
        Configured AIChatOrchestrator instance
    """
    gemini_client_impl.register()
    ai_client = ai_client_api.get_client(api_key=gemini_api_key)

    from slack_impl import SlackClient

    chat_client = SlackClient(base_url=slack_base_url, token=slack_token)

    return AIChatOrchestrator(
        ai_client=ai_client,
        chat_client=chat_client,
        system_prompt=system_prompt,
    )
