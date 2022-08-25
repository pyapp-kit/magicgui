from dataclasses import field, dataclass
from typing import Any, Callable, List, Optional
from typing_extensions import Literal
from magicgui.types import WidgetRef, ChoicesType, Undefined, JsonStringFormats


# @dataclass
# class UiField:
#     widget_type: Optional[WidgetRef] = None
#     text: Optional[str] = None
#     visible: bool = field(
#         default=True, metadata={"description": "Whether the field is visible"}
#     )
#     enabled: bool = field(
#         default=True, metadata={"description": "Whether the field is enabled"}
#     )

#     choices: Optional[ChoicesType] = None
#     enum: Optional[ChoicesType] = None  # alias for choices

#     # for numbers
#     min: Optional[float] = field(
#         default=None, metadata={"description": "(Inclusive) Minimum value"}
#     )
#     ge: Optional[float] = field(default=None, metadata={"description": "alias for min"})
#     max: Optional[float] = field(
#         default=None, metadata={"description": "(Inclusive) Maximum value"}
#     )
#     le: Optional[float] = field(default=None, metadata={"description": "alias for max"})
#     step: Optional[float] = field(default=None, metadata={"description": "Step value"})


@dataclass(frozen=True)
class NumericContraints:
    multiple_of: Optional[float] = field(
        default=None,
        metadata=dict(
            description="Restrict number to a multiple of a given number. "
            "May be any positive number.",
            aliases=["multipleOf"],
        ),
    )
    minimum: Optional[float] = field(
        default=None,
        metadata=dict(description="(Inclusive) Minimum value", aliases=["min", "ge"]),
    )
    maximum: Optional[float] = field(
        default=None,
        metadata=dict(description="(Inclusive) Maximum value", aliases=["max", "le"]),
    )
    # note, in JSON schema, these used to be bools, in which
    # case the implication is that the value for min/max should
    # be used here, and removed in min/max.
    exclusive_minimum: Optional[float] = field(
        default=None,
        metadata=dict(
            description="Exclusive minimum value",
            aliases=["exclusiveMinimum", "gt"],
        ),
    )
    exclusive_maximum: Optional[float] = field(
        default=None,
        metadata=dict(
            description="Exclusive maximum value",
            aliases=["exclusiveMaximum", "lt"],
        ),
    )

    # not in json schema, for Decimal types
    max_digits: Optional[int] = field(
        default=None,
        metadata=dict(
            "Maximum number of digits within the decimal. It does not include a zero "
            "before the decimal point or trailing decimal zeroes."
        ),
    )
    decimal_places: Optional[int] = field(
        default=None,
        metadata=dict(
            "Maximum number of decimal places within the decimal.  It does not include "
            "trailing decimal zeroes."
        ),
    )


@dataclass(frozen=True)
class StringContraints:
    min_length: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Minimum string length. Must be a non-negative number",
            aliases=["minLength"],
        ),
    )
    max_length: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Maximum string length. Must be a non-negative number",
            aliases=["maxLength"],
        ),
    )
    regex: Optional[str] = field(
        default=None,
        metadata=dict(
            description="Regular expression pattern",
            aliases=["pattern"],
        ),
    )
    format: JsonStringFormats = field(
        default=None,
        metadata=dict(
            description="Allows for basic semantic identification of certain kinds of "
            "string values that are commonly used. This is primarily used for "
            "JSON Schema conversion; python types should be preferred when possible.",
        ),
    )


@dataclass(frozen=True)
class ArrayContraints:
    min_length: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Minimum length of the list. Must be a non-negative number.",
            aliases=["minLength"],
        ),
    )
    max_length: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Maximum length of the list. Must be a non-negative number.",
            aliases=["maxLength"],
        ),
    )
    unique_items: Optional[bool] = field(
        default=None,
        metadata=dict(
            description="Declares that each of the items in an array must be unique. "
            "In python, this is best implemented as a set.",
            aliases=["uniqueItems"],
        ),
    )


@dataclass(frozen=True)
class WidgetConstraints:
    widget_type: Optional[WidgetRef] = field(
        default=None,
        metadata=dict(
            description="(Override) the type of widget to use for this field.",
        ),
    )
    visible: bool = field(
        default=True,
        metadata=dict(description="Whether the widget is visible"),
    )
    enabled: bool = field(
        default=True,
        metadata=dict(description="Whether the widget is enabled"),
    )
    orientation: Literal[None, "horizontal", "vertical"] = field(
        default=None,
        metadata=dict(description="Orientation of the widget."),
    )
    # gui_only: bool
    # tooltip: str  # alias for FieldInfo.description?


@dataclass(frozen=True)
class ValueConstraints:
    default: Any = field(
        default=Undefined,
        metadata=dict(description="The default value of the field"),
    )
    default_factory: Optional[Callable[[], Any]] = field(
        default=None,
        metadata=dict(
            description="A callable that returns the default value of the field."
        ),
    )
    const: bool = field(
        default=False,
        metadata=dict(
            description="If True, this argument must be the same as the field's "
            "default value if present"
        ),
    )
    enum: Optional[List[Any]] = field(
        default=None,
        metadata=dict(
            description="A list of valid values for this field. Prefer a python enum.",
            aliases=["choices"],
        ),
    )
    # ### From JSON Schema ###
    # any_of

    # ### From Pydantic ###
    # allow_mutation

    # ### From magicgui ###
    # bind
    # nullable: bool  # for stuff like combo boxes and value widgets


@dataclass(frozen=True)
class FieldInfo:
    title: Optional[str] = field(
        default=None,
        metadata=dict(
            description="The title of the field. (If not provided the name of the "
            "field variable is used.)"
        ),
    )
    description: Optional[str] = field(
        default=None,
        metadata=dict(description="The description of the field"),
    )

    # text: str  # confusingly used on buttons, deprecate
    # mode: str | FileDialogMode


@dataclass(frozen=True)
class ContainerOptions:
    layout: str  # for things like containers


@dataclass(frozen=True)
class WidgetOptions(
    NumericContraints,
    StringContraints,
    ArrayContraints,
    WidgetConstraints,
    ValueConstraints,
    FieldInfo,
):
    pass
