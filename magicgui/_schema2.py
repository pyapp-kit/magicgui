from __future__ import annotations

import sys
import warnings
from dataclasses import (
    MISSING,
    Field,
    asdict,
    dataclass,
    field,
    fields,
    is_dataclass,
    replace,
)
from decimal import Decimal
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, Union

from typing_extensions import Annotated, Literal, TypeGuard, get_args, get_origin

from .types import JsonStringFormats, Undefined

if TYPE_CHECKING:
    from typing import Protocol

    import attrs
    import pydantic
    from attrs import Attribute
    from pydantic.fields import ModelField

    class HasAttrs(Protocol):
        __attrs_attrs__: tuple[attrs.Attribute, ...]


_dc_kwargs = {"frozen": True}
if sys.version_info >= (3, 10):
    _dc_kwargs["slots"] = True


@dataclass(**_dc_kwargs)
class UiField:
    """Metadata about a specific widget in a GUI."""

    name: str | None = field(
        default=None,
        metadata=dict(
            description="The name of the field.  This differs from `title` in that "
            "refers to the python name used to refer to this value. e.g. the parameter "
            "name, or field name in a dataclass"
        ),
    )

    # Basic Meta-Data Annotations vocabulary
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-basic-meta
    title: str | None = field(
        default=None,
        metadata=dict(
            description="A short title for the field.  If not provided, "
            "the `name` will be used."
        ),
    )
    description: str | None = field(
        default=None, metadata=dict(description="A description of the field.")
    )
    default: Any = field(
        default=Undefined, metadata=dict(description="The default value for the field.")
    )
    # NOTE: this does not have an analog in JSON Schema
    default_factory: Callable[[], Any] | None = field(
        default=None,
        metadata=dict(
            description="A callable that returns the default value of the field."
        ),
    )

    # Keywords for Any Instance Type
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-any
    type: Any = field(
        default=None, metadata=dict(description="The type annotation of the field.")
    )
    enum: list[Any] | None = field(
        default=None, metadata=dict(description="A list of allowed values.")
    )
    const: Any = field(
        default=Undefined,
        metadata=dict(
            description="A single allowed value. functionally equivalent to an 'enum' "
            "with a single value.",
        ),
    )

    # Keywords for Numeric Instances (number and integer)
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-num
    minimum: float | None = field(
        default=None, metadata=dict(description="The inclusive minimum allowed value.")
    )
    maximum: float | None = field(
        default=None, metadata=dict(description="The inclusive maximum allowed value.")
    )
    exclusive_minimum: float | None = field(
        default=None, metadata=dict(description="The exclusive minimum allowed value.")
    )
    exclusive_maximum: float | None = field(
        default=None, metadata=dict(description="The exclusive maximum allowed value.")
    )
    multiple_of: float | None = field(
        default=None,
        metadata=dict(
            description="The allowed step size. Value is valid if (value / multiple_of)"
            " is an integer."
        ),
    )

    # Keywords for String Instances
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-str
    min_length: int | None = field(
        default=None,
        metadata=dict(description="The minimum allowed length. Must be >= 0."),
    )
    max_length: int | None = field(
        default=None,
        metadata=dict(description="The maximum allowed length. Must be >= 0."),
    )
    pattern: str | None = field(
        default=None, metadata=dict(description="A regex pattern for the value.")
    )
    # NOTE: format is listed in this section, but needn't strictly apply to strings.
    format: JsonStringFormats | None = field(
        default=None, metadata=dict(description="The format of the field.")
    )

    # Keywords for Sequence (Array) Instances
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-arr
    min_items: int | None = field(
        default=None,
        metadata=dict(description="The minimum allowed number of items. Must be >= 0."),
    )
    max_items: int | None = field(
        default=None,
        metadata=dict(description="The maximum allowed number of items. Must be >= 0."),
    )
    unique_items: bool | None = field(
        default=None,
        metadata=dict(description="Whether the items in the list must be unique."),
    )

    # # Keywords for Mapping (Object) Instances
    # # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-obj
    # max_properties: int | None = field(
    #     default=None,
    #     metadata=dict(description="The maximum allowed number of keys. Must be >= 0."),
    # )
    # min_properties: int | None = field(
    #     default=None,
    #     metadata=dict(description="The minimum allowed number of keys. Must be >= 0."),
    # )
    # required: list[str] | None = field(
    #     default=None,
    #     metadata=dict(
    #         description="A list of required keys that must be present in a mapping/object."
    #     ),
    # )

    # UI Specific
    widget: str | None = field(
        default=None,
        metadata=dict(
            description="The name of the widget to use for this field. "
            "If not provided, the widget will be inferred from the type annotation."
        ),
    )
    disabled: bool | None = field(
        default=None,
        metadata=dict(
            description="Whether the widget should be disabled. Marking a field as "
            "read-only will render it greyed out, but its text value will be "
            "selectable. Disabling it will prevent its value to be selected at all."
        ),
    )
    enum_disabled: list[Any] | None = field(
        default=None,
        metadata=dict(
            description="A list of values that should be disabled in a combobox widget."
        ),
    )
    help: str | None = field(
        default=None,
        metadata=dict(
            description="text next to a field to guide the end user filling it."
        ),
    )
    placeholder: str | None = field(
        default=None,
        metadata=dict(
            description="A placeholder string to display when the field is empty."
        ),
    )
    visible: bool | None = field(
        default=None,
        metadata=dict(
            description="Whether the field should be visible in the GUI. "
            "This is useful for hiding fields that are only used for validation."
        ),
    )
    orientation: Literal["horizontal", "vertical"] | None = field(
        default=None,
        metadata=dict(
            description="Orientation of the widget, for things like sliders."
        ),
    )

    def dict(self, include_unset: bool = True) -> dict[str, Any]:
        """Return the field as a dictionary.

        If `include_unset` is `False`, only fields that have been set will be included.
        """
        d = asdict(self)
        if not include_unset:
            d = {
                k: v
                for k, v in d.items()
                if (v is not Undefined if k in ("default", "const") else v is not None)
            }
        return d

    @classmethod
    def from_field(cls, field: Union[Field, ModelField, Attribute]) -> UiField:
        """Create a UiField from a dataclass, attrs, or pydantic Field."""
        if isinstance(field, Field):
            return _uifield_from_dataclass(field)

        attrs = sys.modules.get("attrs")
        if attrs is not None and isinstance(field, attrs.Attribute):
            return _uifield_from_attrs(field)

        pydantic = sys.modules.get("pydantic.fields")
        if pydantic is not None and isinstance(field, pydantic.ModelField):
            return _uifield_from_pydantic(field)

        raise TypeError(f"Cannot convert object of type {type(field)} to a UiField")

    def parse_annotated(self) -> UiField:
        """Extract info from Annotated type if present, and return new field.

        If self.type is not an Annotated type, return self.
        """
        if get_origin(self.type) is not Annotated:
            return self

        origin, *metadata = get_args(self.type)
        kwargs = {}
        for item in metadata:
            if isinstance(item, UiField):
                kwargs.update(item.dict(include_unset=False))

        if (
            self.default is not Undefined
            and kwargs.get("default", Undefined) is not Undefined
        ):
            warnings.warn(
                "Cannot set default value in both type annotation and field. Overriding"
                f" default {kwargs['default']} with {self.default} in field {self.name}"
            )
            kwargs.pop("default", None)
        if self.name is not None and kwargs.get("name") is not None:
            warnings.warn(
                "Cannot set name in both type annotation and field. Overriding"
                f" name {kwargs['name']} with {self.name} in field {self.name}"
            )
            kwargs.pop("name", None)
        return replace(self, type=origin, **kwargs)


_UI_FIELD_NAMES = {f.name for f in fields(UiField)}


def _uifield_from_dataclass(field: Field) -> UiField:
    """Create a UiField from a dataclass field."""
    default = field.default if field.default is not MISSING else Undefined
    dfactory = field.default_factory if field.default_factory is not MISSING else None
    extra = {k: v for k, v in field.metadata.items() if k in _UI_FIELD_NAMES}

    return UiField(
        name=field.name,
        type=field.type,
        default=default,
        default_factory=dfactory,
        **extra,
    )


def _uifield_from_attrs(field: Attribute) -> UiField:
    """Create a UiField from an attrs field."""
    from attrs import NOTHING, Factory

    default = field.default if field.default is not NOTHING else Undefined
    default_factory = None
    if isinstance(default, Factory):  # type: ignore
        default_factory = default.factory  # type: ignore
        default = Undefined

    extra = {k: v for k, v in field.metadata.items() if k in _UI_FIELD_NAMES}

    return UiField(
        name=field.name,
        type=field.type,
        default=default,
        default_factory=default_factory,
        **extra,
    )


def _uifield_from_pydantic(model_field: ModelField) -> UiField:
    from pydantic.fields import Undefined as PydanticUndefined

    finfo = model_field.field_info

    extra = {k: v for k, v in finfo.extra.items() if k in _UI_FIELD_NAMES}
    const = finfo.const if finfo.const not in (None, PydanticUndefined) else Undefined
    default = Undefined if finfo.default is PydanticUndefined else finfo.default

    return UiField(
        name=model_field.name,
        title=finfo.title,
        description=finfo.description,
        default=default,
        default_factory=model_field.default_factory,
        type=model_field.outer_type_,
        const=const,
        minimum=finfo.ge,
        maximum=finfo.le,
        exclusive_minimum=finfo.gt,
        exclusive_maximum=finfo.lt,
        multiple_of=finfo.multiple_of,
        min_length=finfo.min_length,
        max_length=finfo.max_length,
        pattern=finfo.regex,
        # format=finfo.format,
        min_items=finfo.min_items,
        max_items=finfo.max_items,
        unique_items=finfo.unique_items,
        **extra,
    )


class _ContainerFields:
    autofocus: str | None = field(
        default=None,
        metadata=dict(description="Name of a field that should be autofocused on."),
    )
    labels: list[str] | bool | None = field(
        default=None,
        metadata=dict(
            description="If True, all fields will be labeled. If False, no fields will "
            "be labeled. If a list, only the fields in the list will be labeled."
        ),
    )


# UNUSED from JSON-schema

# deprecated: bool = field(default=False, metadata=dict(description="Whether the field is deprecated."))
# read_only: bool = field(default=False, metadata=dict(description="Whether the field is read-only. If True, the value of the instance is managed exclusively by the owning authority, and attempts by an application to modify the value of this property are expected to be ignored or rejected by that owning authority"))
# write_only: bool = field(default=False, metadata=dict(description="Whether the field is write-only. If True the value is never present when the instance is retrieved from the owning authority"))
# examples: list = field(metadata=dict(description="A list of examples for the field."))


# max_contains: int | None = field(
#     default=None,
#     metadata=dict(
#         description="The maximum number of times that a given item is allowed to appear in the list. Must be >= 0."
#     ),
# )
# min_contains: int | None = field(
#     default=None,
#     metadata=dict(
#         description="The minimum number of times that a given item is allowed to appear in the list. Must be >= 0."
#     ),
# )
# contains: Any | None = field(
#     default=None,
#     metadata=dict(
#         description="A schema that must be satisfied by at least one item in the list."
#     ),
# )

# dependent_required: dict[str, list[str]] | None = field(
#     default=None,
#     metadata=dict(
#         description="A mapping of property names to lists of required properties. If the property is present, the listed properties are also required."
#     ),
# )

# items: JsonSchema = field(metadata=dict(description="The field for items in a list."))
# properties: Dict[str, JsonSchema] = field(metadata=dict(description="The field for properties in a dict."))
# additionalProperties: bool = field(metadata=dict(description="Whether additional properties are allowed."))

# "allOf", "anyOf", "oneOf", "not", "if", "then", "else"
# "additionalItems", "propertyNames",
# "patternProperties"


class ConstraintError(TypeError):
    ...


def validate(self, strict: bool = False) -> None:
    """Validate the field and its constraints."""
    if self.type is None:
        return
    # TODO:
    errs = []
    if self.minimum is not None:
        if strict and not issubclass(self.type, (int, float, Decimal)):
            errs.append(
                ConstraintError(
                    f"Type {self.type} is not numeric, and does not support the "
                    "'minimum' constraint."
                )
            )
        elif not hasattr(self.type, "__ge__"):
            errs.append(
                ConstraintError(
                    f"Type {self.type} lacks a `__ge__` method, and does not "
                    "support the 'minimum' constraint."
                )
            )
    if self.maximum is not None and not hasattr(self.type, "__le__"):
        errs.append(
            ConstraintError(
                f"Type {self.type} lacks a `__le__` method, and does not "
                "support the 'maximum' constraint."
            )
        )
    if self.exclusive_minimum is not None and not hasattr(self.type, "__gt__"):
        errs.append(
            ConstraintError(
                f"Type {self.type} lacks a `__gt__` method, and does not "
                "support the 'exclusive_minimum' constraint."
            )
        )
    if self.exclusive_maximum is not None and not hasattr(self.type, "__lt__"):
        errs.append(
            ConstraintError(
                f"Type {self.type} lacks a `__lt__` method, and does not "
                "support the 'exclusive_maximum' constraint."
            )
        )
    if self.multiple_of is not None and not hasattr(self.type, "__mod__"):
        errs.append(
            ConstraintError(
                f"Type {self.type} lacks a `__mod__` method, and does not "
                "support the 'multiple_of' constraint."
            )
        )
    return errs


def _is_attrs_model(obj: Any) -> TypeGuard[HasAttrs]:
    return getattr(obj, "__attrs_attrs__", None) is not None


def _get_pydantic_model(cls: type) -> type[pydantic.BaseModel] | None:
    pydantic = sys.modules.get("pydantic")
    if pydantic is not None:
        if isinstance(cls, type) and issubclass(cls, pydantic.BaseModel):
            return cls
        elif isinstance(cls, pydantic.BaseModel):
            return type(cls)
        elif hasattr(cls, "__pydantic_model__"):
            return _get_pydantic_model(cls.__pydantic_model__)  # type: ignore
    return None


def _get_function_defaults(func: FunctionType) -> Dict[str, Any]:
    # extracted bit from inspect.signature... ~20x faster
    pos_count = func.__code__.co_argcount
    arg_names = func.__code__.co_varnames

    defaults = func.__defaults__ or ()

    non_default_count = pos_count - len(defaults)
    positional_args = arg_names[:pos_count]

    output = {
        name: defaults[offset]
        for offset, name in enumerate(positional_args[non_default_count:])
    }
    if func.__kwdefaults__:
        output.update(func.__kwdefaults__)
    return output


def _ui_fields_from_annotation(cls) -> Iterator[UiField]:
    # fallback for typed dict, named tuples, & functions

    annotations: dict = getattr(cls, "__annotations__", {})
    if not annotations and isinstance(annotations, dict):
        raise TypeError(
            f"Cannot create  from object {type(cls)} without `__annotations__`"
        )

    # named tuples have _fields and _field_defaults
    field_names = cls._fields if hasattr(cls, "_fields") else annotations
    if isinstance(cls, FunctionType):
        defaults = _get_function_defaults(cls)
    else:
        defaults = getattr(cls, "_field_defaults", {})

    for name in field_names:
        field = UiField(
            name=name,
            type=annotations.get(name),
            default=defaults.get(name, Undefined),
        )
        yield field.parse_annotated()


def iter_ui_fields(object: Any, use_annotations: bool = True) -> Iterator[UiField]:

    if is_dataclass(object):
        for df in fields(object):
            yield _uifield_from_dataclass(df)
        return

    if _is_attrs_model(object):
        for af in object.__attrs_attrs__:
            yield _uifield_from_attrs(af)
        return

    model = _get_pydantic_model(object)
    if model is not None:
        for pf in model.__fields__.values():
            yield _uifield_from_pydantic(pf)
        return

    if use_annotations:
        if hasattr(object, "__annotations__"):
            yield from _ui_fields_from_annotation(object)
            return

        # if this is an instance, try the class
        if not isinstance(object, type) and hasattr(type(object), "__annotations__"):
            yield from _ui_fields_from_annotation(type(object))
            return

    raise TypeError(f"{object} is not a dataclass, attrs, or pydantic, model")
