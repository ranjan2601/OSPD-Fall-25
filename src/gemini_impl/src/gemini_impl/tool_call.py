"""Concrete implementation of ToolCall for Gemini."""

from dataclasses import dataclass
from typing import Any, Dict

import ai_client_api
from ai_client_api.client import ToolCall


@dataclass
class ToolCallImpl(ToolCall):
    """Concrete implementation of the ToolCall ABC."""

    _tool_name: str
    _tool_args: Dict[str, Any]
    _tool_id: str

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
        _tool_name=tool_name,
        _tool_args=tool_args,
        _tool_id=tool_id,
    )


def register() -> None:
    """Register this implementation with ai_client_api."""
    ai_client_api.get_tool_call = get_tool_call_impl
