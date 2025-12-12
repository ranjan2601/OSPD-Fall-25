"""Core orchestration logic for AI-Chat integration."""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class AIChatOrchestrator:
    """Orchestrates message flow between chat platforms and AI services."""

    def __init__(
        self,
        ai_client: Any,
        chat_client: Any,
        system_prompt: str = "You are a helpful AI assistant in a chat channel.",
    ) -> None:
        """Initialize orchestrator with AI and chat clients.

        Args:
            ai_client: Instance of AIInterface
            chat_client: Instance of ChatInterface
            system_prompt: System instruction for the AI model
        """
        self.ai_client = ai_client
        self.chat_client = chat_client
        self.system_prompt = system_prompt

        # Telemetry metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency_seconds": 0.0,
            "ai_generation_time": 0.0,
            "chat_send_time": 0.0,
        }

    def get_metrics(self) -> dict[str, Any]:
        """Return current telemetry metrics.

        Returns:
            Dictionary containing request counts, success/failure rates, and latency stats
        """
        total = self.metrics["total_requests"]
        if total == 0:
            return {**self.metrics, "success_rate": 0.0, "average_latency_seconds": 0.0}

        return {
            **self.metrics,
            "success_rate": self.metrics["successful_requests"] / total,
            "failure_rate": self.metrics["failed_requests"] / total,
            "average_latency_seconds": self.metrics["total_latency_seconds"] / total,
            "average_ai_time_seconds": self.metrics["ai_generation_time"] / total,
            "average_chat_time_seconds": self.metrics["chat_send_time"] / total,
        }

    def handle_message(self, channel_id: str, message_id: str) -> bool:
        """Process a chat message and respond with AI-generated content.

        Args:
            channel_id: ID of the chat channel
            message_id: ID of the message to process

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        self.metrics["total_requests"] += 1

        try:
            # Fetch message from chat
            message = self.chat_client.get_message(channel_id, message_id)
            user_input = message.content

            if not user_input or not user_input.strip():
                logger.warning("Empty message content")
                self.metrics["failed_requests"] += 1
                return False

            # Generate AI response with timing
            ai_start = time.time()
            ai_response = self.ai_client.generate_response(
                user_input=user_input,
                system_prompt=self.system_prompt,
                response_schema=None,
            )
            ai_duration = time.time() - ai_start
            self.metrics["ai_generation_time"] += ai_duration

            response_text = str(ai_response) if isinstance(ai_response, dict) else str(ai_response)

            # Send message with timing
            chat_start = time.time()
            success = bool(self.chat_client.send_message(channel_id, response_text))
            chat_duration = time.time() - chat_start
            self.metrics["chat_send_time"] += chat_duration

            if success:
                self.metrics["successful_requests"] += 1
            else:
                self.metrics["failed_requests"] += 1

            return success

        except (ValueError, RuntimeError) as e:
            logger.error("Error handling message: %s", e)
            self.metrics["failed_requests"] += 1
            return False
        except Exception as e:
            logger.exception("Unexpected error: %s", e)
            self.metrics["failed_requests"] += 1
            return False
        finally:
            # Track total latency
            total_duration = time.time() - start_time
            self.metrics["total_latency_seconds"] += total_duration
            logger.info(
                "Request completed - channel: %s, message: %s, latency: %.3fs, "
                "ai_time: %.3fs, chat_time: %.3fs, success: %s",
                channel_id,
                message_id,
                total_duration,
                self.metrics["ai_generation_time"],
                self.metrics["chat_send_time"],
                self.metrics["successful_requests"] > 0,
            )

    def process_direct(self, channel_id: str, user_input: str) -> str | None:
        """Process user input directly without fetching from chat.

        Args:
            channel_id: ID of the chat channel
            user_input: User's message text

        Returns:
            AI response text, or None if error occurred
        """
        start_time = time.time()
        self.metrics["total_requests"] += 1

        try:
            # Generate AI response with timing
            ai_start = time.time()
            ai_response = self.ai_client.generate_response(
                user_input=user_input,
                system_prompt=self.system_prompt,
                response_schema=None,
            )
            ai_duration = time.time() - ai_start
            self.metrics["ai_generation_time"] += ai_duration

            response_text = str(ai_response) if isinstance(ai_response, dict) else str(ai_response)

            # Send message with timing
            chat_start = time.time()
            success = bool(self.chat_client.send_message(channel_id, response_text))
            chat_duration = time.time() - chat_start
            self.metrics["chat_send_time"] += chat_duration

            if success:
                self.metrics["successful_requests"] += 1
            else:
                self.metrics["failed_requests"] += 1

            return response_text if success else None

        except Exception as e:
            logger.exception("Error processing direct input: %s", e)
            self.metrics["failed_requests"] += 1
            return None
        finally:
            # Track total latency
            total_duration = time.time() - start_time
            self.metrics["total_latency_seconds"] += total_duration
            logger.info(
                "Direct request completed - channel: %s, latency: %.3fs, ai_time: %.3fs, chat_time: %.3fs, success: %s",
                channel_id,
                total_duration,
                ai_duration if "ai_duration" in locals() else 0.0,
                chat_duration if "chat_duration" in locals() else 0.0,
                self.metrics["successful_requests"] > self.metrics["failed_requests"],
            )
