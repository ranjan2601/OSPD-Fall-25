"""Discord Gateway Bot - Runs alongside the orchestrator service.

This module provides Discord WebSocket Gateway integration to listen for
messages and respond automatically using the orchestrator.
"""

import logging
import os
from typing import Any

import discord
from discord.ext import commands

from orchestrator_service.api import get_discord_orchestrator

logger = logging.getLogger(__name__)


class DiscordBot:
    """Discord Gateway bot that listens for messages and responds via orchestrator."""

    def __init__(self, token: str) -> None:
        """Initialize the Discord bot.

        Args:
            token: Discord bot token
        """
        self.token = token

        # Create bot with required intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read message content
        intents.messages = True
        intents.guilds = True

        self.bot = commands.Bot(command_prefix="!", intents=intents)
        self.setup_events()

    def setup_events(self) -> None:
        """Set up bot event handlers."""

        @self.bot.event
        async def on_ready() -> None:
            """Called when bot successfully connects."""
            logger.info(f"Discord bot logged in as {self.bot.user}")
            logger.info(f"Bot is in {len(self.bot.guilds)} guilds")

        @self.bot.event
        async def on_message(message: discord.Message) -> None:
            """Handle incoming messages.

            Args:
                message: Discord message object
            """
            # Ignore messages from the bot itself
            if message.author == self.bot.user:
                return

            # Ignore DMs (only respond in guild channels)
            if not message.guild:
                return

            # Ignore bot commands (starting with !)
            if message.content.startswith("!"):
                await self.bot.process_commands(message)
                return

            user_input = message.content.strip()
            if not user_input:
                return

            channel_name = getattr(message.channel, "name", "DM")
            logger.info(f"Discord message in #{channel_name}: {user_input[:50]}...")

            # Process through orchestrator
            try:
                orchestrator = get_discord_orchestrator()
                response = orchestrator.process_direct(channel_id=str(message.channel.id), user_input=user_input)

                if response:
                    logger.info(f"Response sent to Discord #{channel_name}")
                    # Response already sent via Discord REST API in orchestrator
                    # But we can also send via discord.py as backup:
                    # await message.channel.send(response)
                else:
                    await message.channel.send("Sorry, I couldn't process that request.")
                    logger.error("No response from orchestrator")

            except Exception as e:
                logger.exception(f"Error processing Discord message: {e}")
                await message.channel.send("Sorry, an error occurred while processing your request.")

        @self.bot.command(name="ping")
        async def ping(ctx: commands.Context[Any]) -> None:
            """Test command to check if bot is responsive."""
            await ctx.send(f"Pong! Latency: {round(self.bot.latency * 1000)}ms")

        @self.bot.command(name="help_bot")
        async def help_bot(ctx: commands.Context[Any]) -> None:
            """Show help message."""
            help_text = """
**AI Discord Bot - Help**

I can help you with Jira tickets and Google Tasks!

**Just type naturally:**
• `get my 5 most recent tickets from jira`
• `show my google tasks`
• `list my recent tasks`

**Keywords:**
• For Jira: "jira", "tickets", "issues"
• For Google Tasks: "google tasks", "tasks", "to-do"

**Commands:**
• `!ping` - Check bot latency
• `!help_bot` - Show this help message
            """
            await ctx.send(help_text)

    async def start(self) -> None:
        """Start the Discord bot."""
        logger.info("Starting Discord Gateway bot...")
        try:
            await self.bot.start(self.token)
        except discord.LoginFailure:
            logger.error("Invalid Discord bot token")
            raise
        except Exception as e:
            logger.exception(f"Discord bot error: {e}")
            raise

    async def close(self) -> None:
        """Close the Discord bot connection."""
        logger.info("Closing Discord bot...")
        await self.bot.close()


# Global bot instance
_discord_bot: DiscordBot | None = None


def get_discord_bot() -> DiscordBot:
    """Get or create the Discord bot instance.

    Returns:
        DiscordBot instance
    """
    global _discord_bot
    if _discord_bot is None:
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable not set")
        _discord_bot = DiscordBot(token)
    return _discord_bot


async def start_discord_bot() -> None:
    """Start the Discord bot in the background."""
    bot = get_discord_bot()
    await bot.start()
