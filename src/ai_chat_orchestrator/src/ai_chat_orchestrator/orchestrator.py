"""Core orchestration logic for AI-Chat integration."""

import logging
import time
from typing import Any

from tickets_api import TicketStatus

logger = logging.getLogger(__name__)


class AIChatOrchestrator:
    """Orchestrates message flow between chat platforms and AI services."""

    def __init__(
        self,
        ai_client: Any,
        chat_client: Any,
        system_prompt: str = "You are a helpful AI assistant in a chat channel.",
        ticket_client: Any | None = None,
    ) -> None:
        """Initialize orchestrator with AI and chat clients.

        Args:
            ai_client: Instance of AIInterface
            chat_client: Instance of ChatInterface
            system_prompt: System instruction for the AI model
            ticket_client: Optional ticketing client (Jira/Google Tasks) for AI function calling
        """
        self.ai_client = ai_client
        self.chat_client = chat_client
        self.ticket_client = ticket_client

        # Enhance system prompt with ticket capabilities if ticket_client is available
        if ticket_client:
            self.system_prompt = f"""{system_prompt}

You have access to a ticketing/task management system (which could be Jira, Google Tasks, or similar).
When users ask about tickets, tasks, or to-dos, you can:
- List recent tickets/tasks: Respond with EXACTLY: GET_TICKETS:limit=<number>
- Search tickets/tasks by status: Respond with EXACTLY: SEARCH_TICKETS:status=<status>
- Get specific ticket/task: Respond with EXACTLY: GET_TICKET:id=<ticket_id>

After receiving ticket/task data, provide a natural language summary or answer based on what the user asked.
Valid statuses: open, in_progress, closed

IMPORTANT: When users ask about "tasks" or "to-dos" or "Google Tasks", they are referring to tickets in the system. Use the same commands above.
"""
        else:
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
            messages = self.chat_client.get_messages(channel_id, limit=100)
            message = next((m for m in messages if m.id == message_id), None)

            if not message:
                logger.warning(f"Message {message_id} not found in channel {channel_id}")
                self.metrics["failed_requests"] += 1
                return False

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

            # Check if AI response is a ticket request
            if self.ticket_client and self._is_ticket_request(response_text):
                ticket_data = self._handle_ticket_request(response_text)
                if ticket_data:
                    # Ask AI to summarize the ticket data
                    ai_summary_start = time.time()
                    summary_response = self.ai_client.generate_response(
                        user_input=f"Original request: {user_input}\n\nTicket data:\n{ticket_data}\n\nPlease provide a natural language summary based on what the user asked.",
                        system_prompt=self.system_prompt,
                        response_schema=None,
                    )
                    ai_summary_duration = time.time() - ai_summary_start
                    self.metrics["ai_generation_time"] += ai_summary_duration
                    response_text = (
                        str(summary_response) if isinstance(summary_response, dict) else str(summary_response)
                    )

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

            # Check if AI response is a ticket request
            if self.ticket_client and self._is_ticket_request(response_text):
                ticket_data = self._handle_ticket_request(response_text)
                if ticket_data:
                    # Ask AI to summarize the ticket data
                    ai_summary_start = time.time()
                    summary_response = self.ai_client.generate_response(
                        user_input=f"Original request: {user_input}\n\nTicket data:\n{ticket_data}\n\nPlease provide a natural language summary based on what the user asked.",
                        system_prompt=self.system_prompt,
                        response_schema=None,
                    )
                    ai_summary_duration = time.time() - ai_summary_start
                    self.metrics["ai_generation_time"] += ai_summary_duration
                    response_text = (
                        str(summary_response) if isinstance(summary_response, dict) else str(summary_response)
                    )

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

    def _is_ticket_request(self, response: str) -> bool:
        """Check if AI response contains a ticket function call."""
        commands = ["GET_TICKETS:", "SEARCH_TICKETS:", "GET_TICKET:"]
        return any(cmd in response for cmd in commands)

    def _handle_ticket_request(self, response: str) -> str | None:
        """Parse and execute ticket function calls from AI response."""
        if not self.ticket_client:
            return None

        try:
            # Parse GET_TICKETS:limit=N
            if "GET_TICKETS:" in response:
                limit_str = response.split("GET_TICKETS:limit=")[1].split()[0].strip()
                limit = int(limit_str)
                tickets = self.ticket_client.search_tickets(query=None, status=None)
                tickets_list = list(tickets)[:limit] if hasattr(tickets, "__iter__") else tickets[:limit]
                return self._format_tickets(tickets_list)

            # Parse SEARCH_TICKETS:status=<status>
            elif "SEARCH_TICKETS:status=" in response:
                status = response.split("SEARCH_TICKETS:status=")[1].split()[0].strip()
                # Map status string to enum if needed

                status_map = {
                    "open": TicketStatus.OPEN,
                    "in_progress": TicketStatus.IN_PROGRESS,
                    "closed": TicketStatus.CLOSED,
                }
                ticket_status = status_map.get(status.lower())
                if ticket_status:
                    tickets = self.ticket_client.search_tickets(query=None, status=ticket_status)
                    return self._format_tickets(tickets)

            # Parse GET_TICKET:id=<id>
            elif "GET_TICKET:id=" in response:
                ticket_id = response.split("GET_TICKET:id=")[1].split()[0].strip()
                ticket = self.ticket_client.get_ticket(ticket_id)
                if ticket:
                    return self._format_tickets([ticket])

        except Exception as e:
            logger.error(f"Error handling ticket request: {e}")
            return f"Error fetching tickets: {e}"

        return None

    def _format_tickets(self, tickets: list[Any]) -> str:
        """Format ticket list as a readable string."""
        if not tickets:
            return "No tickets found."

        result = []
        for ticket in tickets:
            result.append(
                f"ID: {ticket.id}\n"
                f"Title: {ticket.title}\n"
                f"Status: {ticket.status.value if hasattr(ticket.status, 'value') else ticket.status}\n"
                f"Description: {ticket.description}\n"
                f"---"
            )
        return "\n".join(result)
