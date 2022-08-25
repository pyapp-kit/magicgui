from dataclasses import dataclass, field, fields
from typing import Any, Callable, Dict, List, Optional, Set, Union

from typing_extensions import Literal

from magicgui.types import JsonStringFormats, Undefined, WidgetRef
from magicgui.widgets._bases.value_widget import ValueWidget


@dataclass(frozen=True)
class NumericContraints:
    multiple_of: Optional[float] = field(
        default=None,
        metadata=dict(
            description="Restrict number to a multiple of a given number. "
            "May be any positive number.",
            aliases=["multipleOf", "step"],
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
            description="Maximum number of digits within the decimal. It does not "
            "include a zero before the decimal point or trailing decimal zeroes."
        ),
    )
    decimal_places: Optional[int] = field(
        default=None,
        metadata=dict(
            descripion="Maximum number of decimal places within the decimal. It does "
            "not include trailing decimal zeroes."
        ),
    )

    # SLIDER WIDGET STUFF
    # readout
    # tracking


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
        metadata=dict(description="The default value of the field", aliases=["value"]),
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

    # ### From magicgui ###
    bind: Union[Callable[[ValueWidget], Any], Any, None] = field(
        default=None,
        metadata=dict(
            description="A value or callable bind to the value of the field. If a "
            "callable, it will be called (with one argument, the ValueWidget), whenever"
            " the value of the field is requested."
        ),
    )
    # nullable: bool  # for stuff like combo boxes and value widgets

    # ### From JSON Schema ###
    # any_of

    # ### From Pydantic ###
    # allow_mutation


@dataclass(frozen=True)
class FieldInfo:
    title: Optional[str] = field(
        default=None,
        metadata=dict(
            description="The title of the field. (If not provided the name of the "
            "field variable is used.)",
            aliases=["label", "text"],
        ),
    )
    description: Optional[str] = field(
        default=None,
        metadata=dict(
            description="The description of the field",
            aliases=["tooltip"],
        ),
    )
    button_text: Optional[str] = field(
        default=None,
        metadata=dict(description="The text of a button", aliases=["text"]),
    )
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


FIELDS: Set[str] = set()
ALIASES: Dict[str, str] = {}

for field_info in fields(WidgetOptions):
    FIELDS.add(field_info.name)
    for alias in field_info.metadata.get("aliases", []):
        ALIASES[alias] = field_info.name


def _field(**kwargs):
    _kwargs = dict(kwargs)
    for key in kwargs:
        if key not in FIELDS:
            if key in ALIASES:
                _kwargs[ALIASES[key]] = _kwargs.pop(key)
            elif key == "allow_multiple":
                _kwargs.pop(key)
                _kwargs["widget_type"] = "Select"
                # TODO: add a warning
            else:
                raise ValueError(f"{key} is not a valid field")
    return WidgetOptions(**_kwargs)
