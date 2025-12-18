"""Core orchestration logic for AI-Chat integration."""

import logging
import re
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
        jira_client: Any | None = None,
        gtasks_client: Any | None = None,
    ) -> None:
        """Initialize orchestrator with AI and chat clients.

        Args:
            ai_client: Instance of AIInterface
            chat_client: Instance of ChatInterface
            system_prompt: System instruction for the AI model
            ticket_client: Optional ticketing client (legacy, for backward compatibility)
            jira_client: Optional Jira client for ticket management
            gtasks_client: Optional Google Tasks client for task management
        """
        self.ai_client = ai_client
        self.chat_client = chat_client

        self.jira_client = jira_client or ticket_client
        self.gtasks_client = gtasks_client
        self.ticket_client = ticket_client

        self.conversation_history: dict[str, list[dict[str, str]]] = {}

        if self.jira_client or self.gtasks_client:
            systems = []
            if self.jira_client:
                systems.append("Jira")
            if self.gtasks_client:
                systems.append("Google Tasks")

            system_list = " and ".join(systems)

            self.system_prompt = f"""{system_prompt}

You have access to multiple ticketing/task management systems: {system_list}.

When users ask about tickets or tasks, determine which system they're referring to:
- If they mention "Jira" or "tickets", use: JIRA:GET_TICKETS:limit=<number> or JIRA:SEARCH_TICKETS:status=<status> or JIRA:GET_TICKET:id=<id>
- If they mention "Google Tasks", "tasks", or "to-dos", use: GTASKS:GET_TICKETS:limit=<number> or GTASKS:SEARCH_TICKETS:status=<status> or GTASKS:GET_TICKET:id=<id>

CRITICAL RULE FOR "SUMMARIZE" REQUESTS:
- When user says "summarize them", "summarize it", or similar AFTER viewing tickets:
  * DO NOT output any JIRA: or GTASKS: commands
  * DO NOT re-fetch the tickets
  * Look at conversation history for the ticket data
  * Provide a brief natural language summary (2-3 sentences highlighting key themes, statuses, priorities)
- Only use ticket commands when user explicitly asks for NEW or DIFFERENT tickets

After receiving data, provide a natural language summary or answer based on what the user asked.
Valid statuses: open, in_progress, closed

FORMATTING RULES for Slack/Discord:
- Use simple, clean formatting
- Put each bullet point on a NEW LINE with a blank line before it
- Example format:
  Summary sentence here.

  • First point

  • Second point

  • Third point

IMPORTANT: Always prefix commands with the system name (JIRA: or GTASKS:) to specify which system to query.
"""
        else:
            self.system_prompt = system_prompt

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

            ai_start = time.time()
            ai_response = self.ai_client.generate_response(
                user_input=user_input,
                system_prompt=self.system_prompt,
                response_schema=None,
            )
            ai_duration = time.time() - ai_start
            self.metrics["ai_generation_time"] += ai_duration

            response_text = str(ai_response) if isinstance(ai_response, dict) else str(ai_response)

            if self.ticket_client and self._is_ticket_request(response_text):
                ticket_data, _ = self._handle_ticket_request(response_text)
                if ticket_data:
                    response_text = ticket_data

            response_text = self._clean_markdown_formatting(response_text)

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
            if channel_id not in self.conversation_history:
                self.conversation_history[channel_id] = []

            history_context = ""
            if self.conversation_history[channel_id]:
                history_context = "\n\nRecent conversation history:\n"
                for entry in self.conversation_history[channel_id][-5:]:
                    history_context += f"User: {entry['user']}\nAssistant: {entry['assistant']}\n"

            ai_start = time.time()
            full_user_input = user_input
            if history_context:
                full_user_input = f"{history_context}\n\nCurrent message: {user_input}"

            ai_response = self.ai_client.generate_response(
                user_input=full_user_input,
                system_prompt=self.system_prompt,
                response_schema=None,
            )
            ai_duration = time.time() - ai_start
            self.metrics["ai_generation_time"] += ai_duration

            response_text = str(ai_response) if isinstance(ai_response, dict) else str(ai_response)

            ticket_metadata = None
            if (self.ticket_client or self.jira_client or self.gtasks_client) and self._is_ticket_request(
                response_text
            ):
                ticket_data, ticket_metadata = self._handle_ticket_request(response_text)
                if ticket_data:
                    response_text = ticket_data

            response_text = self._clean_markdown_formatting(response_text)

            chat_start = time.time()
            success = bool(self.chat_client.send_message(channel_id, response_text))
            chat_duration = time.time() - chat_start
            self.metrics["chat_send_time"] += chat_duration

            if success:
                self.metrics["successful_requests"] += 1
                self.conversation_history[channel_id].append({"user": user_input, "assistant": response_text})
                if len(self.conversation_history[channel_id]) > 10:
                    self.conversation_history[channel_id] = self.conversation_history[channel_id][-10:]
            else:
                self.metrics["failed_requests"] += 1

            return response_text if success else None

        except Exception as e:
            logger.exception("Error processing direct input: %s", e)
            self.metrics["failed_requests"] += 1
            return None
        finally:
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
        commands = ["GET_TICKETS:", "SEARCH_TICKETS:", "GET_TICKET:", "JIRA:", "GTASKS:"]
        return any(cmd in response for cmd in commands)

    def _handle_ticket_request(self, response: str) -> tuple[str | None, dict[str, Any] | None]:
        """Parse and execute ticket function calls from AI response.

        Returns:
            Tuple of (formatted_data, metadata) where metadata contains system_name, count, etc.
        """
        client = None
        system_name = ""

        if "JIRA:" in response:
            client = self.jira_client
            system_name = "Jira"
            response = response.replace("JIRA:", "")
        elif "GTASKS:" in response:
            client = self.gtasks_client
            system_name = "Google Tasks"
            response = response.replace("GTASKS:", "")
        else:
            client = self.ticket_client
            system_name = "ticket system"

        if not client:
            return (
                f"Sorry, {system_name} is not currently available. Please contact your administrator to enable this feature.",
                None,
            )

        try:
            if "GET_TICKETS:" in response:
                limit_str = response.split("GET_TICKETS:limit=")[1].split()[0].strip()
                limit = int(limit_str)
                tickets = client.search_tickets(query=None, status=None)
                tickets_list = list(tickets)[:limit] if hasattr(tickets, "__iter__") else tickets[:limit]
                formatted = self._format_tickets(tickets_list, count=limit)
                metadata = {"system": system_name, "count": len(tickets_list), "type": "recent"}
                return formatted, metadata

            elif "SEARCH_TICKETS:status=" in response:
                status = response.split("SEARCH_TICKETS:status=")[1].split()[0].strip()

                status_map = {
                    "open": TicketStatus.OPEN,
                    "in_progress": TicketStatus.IN_PROGRESS,
                    "closed": TicketStatus.CLOSED,
                }
                ticket_status = status_map.get(status.lower())
                if ticket_status:
                    tickets = client.search_tickets(query=None, status=ticket_status)
                    tickets_list = list(tickets) if hasattr(tickets, "__iter__") else tickets
                    formatted = self._format_tickets(tickets_list)
                    metadata = {"system": system_name, "count": len(tickets_list), "type": "search", "status": status}
                    return formatted, metadata

            elif "GET_TICKET:id=" in response:
                ticket_id = response.split("GET_TICKET:id=")[1].split()[0].strip()
                ticket = client.get_ticket(ticket_id)
                if ticket:
                    formatted = self._format_tickets([ticket])
                    metadata = {"system": system_name, "count": 1, "type": "single", "id": ticket_id}
                    return formatted, metadata

        except Exception as e:
            logger.error(f"Error handling {system_name} request: {e}")
            return (
                f"Sorry, I couldn't fetch data from {system_name} right now. The service might be temporarily unavailable. Please try again later.",
                None,
            )

        return None, None

    def _format_tickets(self, tickets: list[Any], count: int | None = None) -> str:
        """Format ticket list as a clean numbered list.

        Args:
            tickets: List of ticket objects to format
            count: Optional requested count for header message

        Returns:
            Formatted string with numbered tickets
        """
        if not tickets:
            return "No tickets found."

        num_tickets = len(tickets)
        if count and count == num_tickets:
            header = f"Here are your {num_tickets} most recent tickets:"
        elif count and count > num_tickets:
            header = f"Here are your {num_tickets} most recent tickets (you requested {count}, but only {num_tickets} available):"
        else:
            header = f"Here are your {num_tickets} tickets:"

        result = [header]
        for i, ticket in enumerate(tickets, 1):
            status_str = ticket.status.value if hasattr(ticket.status, "value") else ticket.status
            result.append(
                f"{i}. {ticket.title} (ID: {ticket.id})\n   Status: {status_str}\n   Description: {ticket.description}"
            )

        return "\n".join(result)

    def _clean_markdown_formatting(self, text: str) -> str:
        """Minimal cleanup of AI responses - Gemini handles most formatting via system prompt.

        Just removes bold markdown as Slack/Discord render it oddly.
        """
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)

        return text.strip()
