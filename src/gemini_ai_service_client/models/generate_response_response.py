from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.generate_response_response_output_type_1 import (
        GenerateResponseResponseOutputType1,
    )


T = TypeVar("T", bound="GenerateResponseResponse")


@_attrs_define
class GenerateResponseResponse:
    """Response model from the AI service.

    Attributes:
        output (GenerateResponseResponseOutputType1 | str): The AI's response (string for conversational, dict for
            structured)
    """

    output: GenerateResponseResponseOutputType1 | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.generate_response_response_output_type_1 import (
            GenerateResponseResponseOutputType1,
        )

        output: dict[str, Any] | str
        if isinstance(self.output, GenerateResponseResponseOutputType1):
            output = self.output.to_dict()
        else:
            output = self.output

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "output": output,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.generate_response_response_output_type_1 import (
            GenerateResponseResponseOutputType1,
        )

        d = dict(src_dict)

        def _parse_output(data: object) -> GenerateResponseResponseOutputType1 | str:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                output_type_1 = GenerateResponseResponseOutputType1.from_dict(data)

                return output_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(GenerateResponseResponseOutputType1 | str, data)

        output = _parse_output(d.pop("output"))

        generate_response_response = cls(
            output=output,
        )

        generate_response_response.additional_properties = d
        return generate_response_response

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
