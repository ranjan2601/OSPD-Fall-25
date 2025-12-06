from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.send_message_response_tool_calls_item import SendMessageResponseToolCallsItem


T = TypeVar("T", bound="SendMessageResponse")


@_attrs_define
class SendMessageResponse:
    """Response model from the AI service.

    Attributes:
        text (str): The AI's response text
        tool_calls (list[SendMessageResponseToolCallsItem] | Unset): List of tool calls from the response
    """

    text: str
    tool_calls: list[SendMessageResponseToolCallsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        text = self.text

        tool_calls: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tool_calls, Unset):
            tool_calls = []
            for tool_calls_item_data in self.tool_calls:
                tool_calls_item = tool_calls_item_data.to_dict()
                tool_calls.append(tool_calls_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "text": text,
            }
        )
        if tool_calls is not UNSET:
            field_dict["tool_calls"] = tool_calls

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.send_message_response_tool_calls_item import SendMessageResponseToolCallsItem

        d = dict(src_dict)
        text = d.pop("text")

        _tool_calls = d.pop("tool_calls", UNSET)
        tool_calls: list[SendMessageResponseToolCallsItem] | Unset = UNSET
        if _tool_calls is not UNSET:
            tool_calls = []
            for tool_calls_item_data in _tool_calls:
                tool_calls_item = SendMessageResponseToolCallsItem.from_dict(tool_calls_item_data)

                tool_calls.append(tool_calls_item)

        send_message_response = cls(
            text=text,
            tool_calls=tool_calls,
        )

        send_message_response.additional_properties = d
        return send_message_response

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
