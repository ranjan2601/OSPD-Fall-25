from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.tool_definition_parameters import ToolDefinitionParameters


T = TypeVar("T", bound="ToolDefinition")


@_attrs_define
class ToolDefinition:
    """Definition of a tool the AI can call.

    Attributes:
        name (str): Tool name
        description (str): What the tool does
        parameters (ToolDefinitionParameters | Unset): JSON Schema for tool parameters
    """

    name: str
    description: str
    parameters: ToolDefinitionParameters | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        parameters: dict[str, Any] | Unset = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = self.parameters.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
            }
        )
        if parameters is not UNSET:
            field_dict["parameters"] = parameters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_definition_parameters import ToolDefinitionParameters

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        _parameters = d.pop("parameters", UNSET)
        parameters: ToolDefinitionParameters | Unset
        if isinstance(_parameters, Unset):
            parameters = UNSET
        else:
            parameters = ToolDefinitionParameters.from_dict(_parameters)

        tool_definition = cls(
            name=name,
            description=description,
            parameters=parameters,
        )

        tool_definition.additional_properties = d
        return tool_definition

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
