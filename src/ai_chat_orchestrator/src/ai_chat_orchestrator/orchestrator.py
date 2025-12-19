"""Core orchestration logic for AI-Chat integration."""

import logging
import re
import time
from typing import Any
from uuid import UUID

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
- If they mention "Jira" or "tickets", use JIRA: prefix
- If they mention "Google Tasks", "tasks", or "to-dos", use GTASKS: prefix

AVAILABLE COMMANDS:

JIRA COMMANDS:

READ Operations:
- JIRA:GET_TICKETS:limit=<number> - Get recent tickets (e.g., "Show me my 5 most recent tickets")
- JIRA:SEARCH_TICKETS:status=<status> - Search by status (e.g., "Show me open tickets")
- JIRA:GET_TICKET:id=<id> - Get specific ticket (e.g., "Show me ticket KAN-123")

WRITE Operations:
- JIRA:CREATE_TICKET:title=<title>|description=<desc>|priority=<priority> - Create new ticket
- JIRA:UPDATE_TICKET:id=<id>|status=<status> - Update ticket status by ID (e.g., "Change ticket KAN-123 to in_progress")
- JIRA:UPDATE_TICKET:title=<title>|status=<status> - Update ticket status by title (e.g., "Change status of Fix login bug to in_progress")
- JIRA:CLOSE_TICKET:id=<id> - Close a ticket by ID (e.g., "Close ticket KAN-123")
- JIRA:CLOSE_TICKET:title=<title> - Close a ticket by title (e.g., "Close Fix login bug")

GTASKS COMMANDS:

READ Operations:
- GTASKS:GET_TICKETS:limit=<number> - Get recent tasks (e.g., "Show me my 5 most recent tasks")
- GTASKS:SEARCH_TICKETS:status=<status> - Search tasks by status (e.g., "Show me open tasks")
- GTASKS:GET_TICKET:id=<id> - Get specific task (e.g., "Show me task abc123")

WRITE Operations:
- GTASKS:CREATE_TICKET:title=<title>|description=<desc> - Create new task
- GTASKS:UPDATE_TICKET:id=<id>|status=<status> - Update task status by ID
- GTASKS:UPDATE_TICKET:title=<title>|status=<status> - Update task status by title
- GTASKS:CLOSE_TICKET:id=<id> - Close a task by ID
- GTASKS:CLOSE_TICKET:title=<title> - Close a task by title

Valid statuses: open, in_progress, closed
Valid priorities: low, medium, high, critical (default: medium if not specified)

COMMAND FORMATTING RULES:
- For CREATE_TICKET: Use pipe | to separate title, description, and optional priority
  * Extract priority from natural language like "high priority", "set priority to critical", "priority: low"
  * Always convert priority to lowercase (high, medium, low, critical)
  * If no priority mentioned, omit the priority parameter (defaults to medium)
- For UPDATE_TICKET: Use pipe | to separate identifier (id= or title=) and status
  * Use id= when user provides exact ticket ID
  * Use title= when user refers to ticket by name (e.g., "change status of Fix login bug")
  * Title matching is case-insensitive and partial matches are allowed
- Example: JIRA:CREATE_TICKET:title=Fix login bug|description=Users cannot log in|priority=high
- Example: JIRA:CREATE_TICKET:title=Update docs|description=Add API docs (priority defaults to medium)
- Example: JIRA:UPDATE_TICKET:id=KAN-123|status=in_progress
- Example: JIRA:UPDATE_TICKET:title=Fix login bug|status=closed

NATURAL LANGUAGE PARSING FOR CREATE_TICKET:
- "Create a high priority ticket..." → priority=high
- "Set the priority to Critical" → priority=critical  
- "titled X with description Y" → extract title and description accurately
- Long descriptions are allowed - capture the full text between quotes or after "description:"

CRITICAL RULE FOR "SUMMARIZE" REQUESTS:
- When user says "summarize them", "summarize it", or similar AFTER viewing tickets:
  * DO NOT output any JIRA: or GTASKS: commands
  * DO NOT re-fetch the tickets
  * Look at conversation history for the ticket data
  * Provide a brief natural language summary (2-3 sentences highlighting key themes, statuses, priorities)
- Only use ticket commands when user explicitly asks for NEW or DIFFERENT tickets

IMPORTANT: When executing a ticket command (GET_TICKETS, SEARCH_TICKETS, CREATE_TICKET, etc.):
- Output ONLY the command itself
- Do NOT include any additional text, explanations, or formatted data
- The system will automatically fetch and format the data for you
- Example: If user asks "show me my recent tickets", respond with ONLY: JIRA:GET_TICKETS:limit=5

FORMATTING RULES for Slack/Discord:
- Use simple, clean formatting
- Put each bullet point on a NEW LINE with a blank line before it
- Example format:
  Summary sentence here.

  • First point

  • Second point

  • Third point

IMPORTANT: Always prefix commands with the system name (JIRA: or GTASKS:) to specify which system to use.
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
        commands = [
            "GET_TICKETS:",
            "SEARCH_TICKETS:",
            "GET_TICKET:",
            "CREATE_TICKET:",
            "UPDATE_TICKET:",
            "CLOSE_TICKET:",
            "JIRA:",
            "GTASKS:",
        ]
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
                ticket_id_str = response.split("GET_TICKET:id=")[1].split()[0].strip()
                try:
                    ticket_id = UUID(ticket_id_str)
                except ValueError:
                    return f"Error: Invalid ticket ID format '{ticket_id_str}'. Expected UUID format.", None
                ticket = client.get_ticket(str(ticket_id))
                if ticket:
                    formatted = self._format_tickets([ticket])
                    metadata = {"system": system_name, "count": 1, "type": "single", "id": str(ticket_id)}
                    return formatted, metadata

            elif "CREATE_TICKET:" in response:
                # Parse: CREATE_TICKET:title=<title>|description=<desc>|priority=<priority>
                parts = response.split("CREATE_TICKET:")[1].strip()
                title = "Untitled"
                description = "No description provided"
                priority_text = ""

                logger.info(f"CREATE_TICKET parsing - raw parts: {parts}")

                # Split by pipe and parse each part
                if "|" in parts:
                    segments = parts.split("|")
                    for segment in segments:
                        segment = segment.strip()
                        if segment.startswith("title="):
                            title = segment.replace("title=", "", 1).strip()
                        elif segment.startswith("description="):
                            description = segment.replace("description=", "", 1).strip()
                        elif segment.startswith("priority="):
                            priority_val = segment.replace("priority=", "", 1).strip().lower()
                            priority_text = f"[PRIORITY: {priority_val.upper()}] "
                            logger.info(f"Priority detected: {priority_val} -> {priority_text}")

                    # Prepend priority to description if specified
                    if priority_text:
                        description = f"{priority_text}{description}"
                else:
                    # Fallback: just title
                    title = parts.replace("title=", "").strip()

                logger.info(f"Final ticket params - title: {title}, description: {description[:100]}...")
                ticket = client.create_ticket(title=title, description=description)
                if ticket:
                    result = f"✓ Ticket created successfully in {system_name}!\n\nID: {ticket.id}\nTitle: {ticket.title}\nStatus: {ticket.status.value if hasattr(ticket.status, 'value') else ticket.status}\nDescription: {ticket.description}"
                    metadata = {"system": system_name, "type": "create", "id": str(ticket.id)}
                    return result, metadata

            elif "UPDATE_TICKET:" in response:
                # Parse: UPDATE_TICKET:id=<id>|status=<status> OR UPDATE_TICKET:title=<title>|status=<status>
                parts = response.split("UPDATE_TICKET:")[1].strip()
                if "|" not in parts:
                    return (
                        "Error: UPDATE_TICKET requires format: id=<id>|status=<status> or title=<title>|status=<status>",
                        None,
                    )

                identifier_part, status_part = parts.split("|", 1)
                new_status = status_part.replace("status=", "").strip()

                status_map = {
                    "open": TicketStatus.OPEN,
                    "in_progress": TicketStatus.IN_PROGRESS,
                    "closed": TicketStatus.CLOSED,
                }
                ticket_status = status_map.get(new_status.lower())

                if not ticket_status:
                    return (
                        f"Error: Invalid status '{new_status}'. Valid statuses: open, in_progress, closed",
                        None,
                    )

                # Determine if using ID or title
                ticket_id = None  # type: ignore[assignment]
                if identifier_part.startswith("id="):
                    # Using ID - handle both UUID (Jira) and string IDs (GTasks)
                    ticket_id_str = identifier_part.replace("id=", "").strip()
                    try:
                        ticket_id = UUID(ticket_id_str)
                    except ValueError:
                        # Not a UUID, use as string (for GTasks)
                        ticket_id = ticket_id_str  # type: ignore[assignment]
                elif identifier_part.startswith("title="):
                    # Using title - search for matching ticket
                    search_title = identifier_part.replace("title=", "").strip().lower()
                    tickets = client.search_tickets(query=None, status=None)
                    tickets_list = list(tickets) if hasattr(tickets, "__iter__") else tickets

                    # Find ticket with matching title (case-insensitive, partial match)
                    matching_ticket = None
                    for ticket in tickets_list:
                        if search_title in ticket.title.lower():
                            matching_ticket = ticket
                            break

                    if not matching_ticket:
                        return (
                            f"Error: No ticket found with title containing '{identifier_part.replace('title=', '').strip()}'",
                            None,
                        )

                    # Handle both UUID and string IDs
                    try:
                        ticket_id = (
                            UUID(matching_ticket.id) if not isinstance(matching_ticket.id, UUID) else matching_ticket.id
                        )
                    except ValueError:
                        ticket_id = matching_ticket.id
                else:
                    return "Error: UPDATE_TICKET requires 'id=' or 'title=' prefix", None

                ticket = client.update_ticket(ticket_id=str(ticket_id), status=ticket_status)
                if ticket:
                    result = f"✓ Ticket updated successfully in {system_name}!\n\nID: {ticket.id}\nTitle: {ticket.title}\nNew Status: {ticket.status.value if hasattr(ticket.status, 'value') else ticket.status}"
                    metadata = {"system": system_name, "type": "update", "id": str(ticket.id)}
                    return result, metadata

            elif "CLOSE_TICKET:" in response:
                # Parse: CLOSE_TICKET:id=<id> OR CLOSE_TICKET:title=<title>
                parts = response.split("CLOSE_TICKET:")[1].strip()

                ticket_id = None  # type: ignore[assignment]
                if parts.startswith("id="):
                    ticket_id_str = parts.replace("id=", "").split()[0].strip()
                    try:
                        ticket_id = UUID(ticket_id_str)
                    except ValueError:
                        # Not a UUID, use as string (for GTasks)
                        ticket_id = ticket_id_str  # type: ignore[assignment]
                elif parts.startswith("title="):
                    # Using title - search for matching ticket
                    search_title = parts.replace("title=", "").strip().lower()
                    tickets = client.search_tickets(query=None, status=None)
                    tickets_list = list(tickets) if hasattr(tickets, "__iter__") else tickets

                    matching_ticket = None
                    for ticket in tickets_list:
                        if search_title in ticket.title.lower():
                            matching_ticket = ticket
                            break

                    if not matching_ticket:
                        return (
                            f"Error: No ticket found with title containing '{parts.replace('title=', '').strip()}'",
                            None,
                        )

                    # Handle both UUID and string IDs
                    try:
                        ticket_id = (
                            UUID(matching_ticket.id) if not isinstance(matching_ticket.id, UUID) else matching_ticket.id
                        )
                    except ValueError:
                        ticket_id = matching_ticket.id
                else:
                    return "Error: CLOSE_TICKET requires 'id=' or 'title=' prefix", None

                ticket = client.update_ticket(ticket_id=str(ticket_id), status=TicketStatus.CLOSED)
                if ticket:
                    result = f"✓ Ticket closed successfully in {system_name}!\n\nID: {ticket.id}\nTitle: {ticket.title}\nStatus: Closed"
                    metadata = {"system": system_name, "type": "close", "id": str(ticket.id)}
                    return result, metadata

        except Exception as e:
            logger.error(f"Error handling {system_name} request: {e}")
            return (
                f"Sorry, I couldn't complete the {system_name} operation right now. Error: {str(e)}",
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

            # Extract priority from description if present
            description = ticket.description
            priority_str = None
            priority_match = re.match(r"^\[PRIORITY: (LOW|MEDIUM|HIGH|CRITICAL)\]\s*", description)
            if priority_match:
                priority_str = priority_match.group(1)
                description = description[priority_match.end() :]  # Remove priority prefix from description

            # Build ticket info
            ticket_info = f"{i}. {ticket.title} (ID: {ticket.id})"
            if priority_str:
                ticket_info += f"\n   Priority: {priority_str}"
            ticket_info += f"\n   Status: {status_str}\n   Description: {description}"

            result.append(ticket_info)

        return "\n".join(result)

    def _clean_markdown_formatting(self, text: str) -> str:
        """Minimal cleanup of AI responses - Gemini handles most formatting via system prompt.

        Just removes bold markdown as Slack/Discord render it oddly.
        """
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)

        return text.strip()
