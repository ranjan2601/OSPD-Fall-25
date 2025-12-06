from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tool_definition import ToolDefinition


T = TypeVar("T", bound="SendMessageRequest")


@_attrs_define
class SendMessageRequest:
    """Request model for sending a message to the AI.

    Attributes:
        user_id (str): Unique identifier for the user
        prompt (str): The user's message/prompt text
        tools (list[ToolDefinition] | None | Unset): Optional list of tool definitions
    """

    user_id: str
    prompt: str
    tools: list[ToolDefinition] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        prompt = self.prompt

        tools: list[dict[str, Any]] | None | Unset
        if isinstance(self.tools, Unset):
            tools = UNSET
        elif isinstance(self.tools, list):
            tools = []
            for tools_type_0_item_data in self.tools:
                tools_type_0_item = tools_type_0_item_data.to_dict()
                tools.append(tools_type_0_item)

        else:
            tools = self.tools

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "prompt": prompt,
            }
        )
        if tools is not UNSET:
            field_dict["tools"] = tools

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_definition import ToolDefinition

        d = dict(src_dict)
        user_id = d.pop("user_id")

        prompt = d.pop("prompt")

        def _parse_tools(data: object) -> list[ToolDefinition] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tools_type_0 = []
                _tools_type_0 = data
                for tools_type_0_item_data in _tools_type_0:
                    tools_type_0_item = ToolDefinition.from_dict(tools_type_0_item_data)

                    tools_type_0.append(tools_type_0_item)

                return tools_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ToolDefinition] | None | Unset, data)

        tools = _parse_tools(d.pop("tools", UNSET))

        send_message_request = cls(
            user_id=user_id,
            prompt=prompt,
            tools=tools,
        )

        send_message_request.additional_properties = d
        return send_message_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
