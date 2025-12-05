"""Concrete implementation of ToolCall for Gemini."""

from typing import Any, Dict

import ai_client_api
from ai_client_api.client import ToolCall


class ToolCallImpl(ToolCall):
    """Concrete implementation of the ToolCall ABC."""

    def __init__(self, tool_name: str, tool_args: Dict[str, Any], tool_id: str) -> None:
        """Initialize a tool call.

        Args:
            tool_name: Name of the tool being called.
            tool_args: Arguments dictionary for the tool.
            tool_id: Unique identifier for this invocation.
        """
        self._tool_name = tool_name
        self._tool_args = tool_args
        self._tool_id = tool_id

    @property
    def tool_name(self) -> str:
        return self._tool_name

    @property
    def tool_args(self) -> Dict[str, Any]:
        return self._tool_args

    @property
    def tool_id(self) -> str:
        return self._tool_id


def get_tool_call_impl(
    tool_name: str, tool_args: Dict[str, Any], tool_id: str
) -> ai_client_api.ToolCall:
    """Factory function for ToolCallImpl."""
    return ToolCallImpl(
        tool_name=tool_name,
        tool_args=tool_args,
        tool_id=tool_id,
    )


def register() -> None:
    """Register this implementation with ai_client_api."""
    ai_client_api.get_tool_call = get_tool_call_impl
