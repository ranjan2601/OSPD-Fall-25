from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MessageDetail")


@_attrs_define
class MessageDetail:
    """Discord message details.

    Attributes:
        id (str): Message ID
        channel_id (str): Channel ID
        sender_id (str): Sender user ID
        sender_name (str): Sender display name
        content (str): Message content
        timestamp (str): Message timestamp
        edited_timestamp (None | str | Unset): Edit timestamp if edited
    """

    id: str
    channel_id: str
    sender_id: str
    sender_name: str
    content: str
    timestamp: str
    edited_timestamp: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        channel_id = self.channel_id

        sender_id = self.sender_id

        sender_name = self.sender_name

        content = self.content

        timestamp = self.timestamp

        edited_timestamp: None | str | Unset
        if isinstance(self.edited_timestamp, Unset):
            edited_timestamp = UNSET
        else:
            edited_timestamp = self.edited_timestamp

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "channel_id": channel_id,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "content": content,
                "timestamp": timestamp,
            }
        )
        if edited_timestamp is not UNSET:
            field_dict["edited_timestamp"] = edited_timestamp

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        channel_id = d.pop("channel_id")

        sender_id = d.pop("sender_id")

        sender_name = d.pop("sender_name")

        content = d.pop("content")

        timestamp = d.pop("timestamp")

        def _parse_edited_timestamp(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        edited_timestamp = _parse_edited_timestamp(d.pop("edited_timestamp", UNSET))

        message_detail = cls(
            id=id,
            channel_id=channel_id,
            sender_id=sender_id,
            sender_name=sender_name,
            content=content,
            timestamp=timestamp,
            edited_timestamp=edited_timestamp,
        )

        message_detail.additional_properties = d
        return message_detail

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
