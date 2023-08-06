from __future__ import annotations

import dataclasses as dc
import sys
import warnings
from dataclasses import dataclass, field
from functools import lru_cache
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Literal,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import Annotated, TypeGuard, get_args, get_origin

from magicgui.types import JsonStringFormats, Undefined, _Undefined

if TYPE_CHECKING:
    from typing import Mapping, Protocol

    import attrs
    import pydantic
    from annotated_types import BaseMetadata
    from attrs import Attribute
    from pydantic.fields import FieldInfo, ModelField

    from magicgui.widgets.bases import ContainerWidget, ValueWidget

    class HasAttrs(Protocol):
        """Protocol for objects that have an ``attrs`` attribute."""

        __attrs_attrs__: tuple[attrs.Attribute, ...]


__all__ = ["build_widget", "get_ui_fields", "UiField"]

SLOTS = {"slots": True} if sys.version_info >= (3, 10) else {}
T = TypeVar("T")


@dataclass(frozen=True, **SLOTS)
class UiField(Generic[T]):
    """Metadata about a specific widget in a GUI."""

    def __post_init__(self) -> None:
        """Coerce Optional[...] to nullable and remove it from the type."""
        if get_origin(self.type) is Union:
            args = get_args(self.type)
            nonnull = tuple(a for a in args if a is not type(None))
            if len(nonnull) < len(args):
                # object.__setattr__ because we are using a frozen dataclass
                object.__setattr__(self, "_original_annotation", self.type)
                object.__setattr__(self, "type", Union[nonnull])
                object.__setattr__(self, "nullable", True)

    name: str | None = field(
        default=None,
        metadata={
            "description": "The name of the field.  This differs from `title` in that "
            "refers to the python name used to refer to this value. e.g. the parameter "
            "name, or field name in a dataclass"
        },
    )

    # Basic Meta-Data Annotations vocabulary
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-a-vocabulary-for-basic-meta
    title: str | None = field(
        default=None,
        metadata={
            "description": "A short title for the field.  If not provided, "
            "the `name` will be used.",
            "aliases": ["label", "text", "button_text"],
        },
    )
    description: str | None = field(
        default=None,
        metadata={"description": "A description of the field.", "aliases": ["tooltip"]},
    )
    default: T = field(  # type: ignore
        default=Undefined,
        metadata={
            "description": "The default value for the field.",
            "aliases": ["value"],
        },
    )
    # NOTE: this does not have an analog in JSON Schema
    default_factory: Callable[[], T] | None = field(
        default=None,
        metadata={
            "description": "A callable that returns the default value of the field."
        },
    )
    # NOTE: this does not have an analog in JSON Schema
    nullable: bool | None = field(
        default=None,
        metadata={
            "description": "Whether the field is nullable. In JSON, this is equivalent "
            "to `type: [<type>, 'null']`"
        },
    )

    # Keywords for Any Instance Type
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-any
    type: object = field(
        default=None, metadata={"description": "The type annotation of the field."}
    )
    enum: list[T] | None = field(
        default=None,
        metadata={"description": "A list of allowed values.", "aliases": ["choices"]},
    )
    const: T = field(  # type: ignore
        default=Undefined,
        metadata={
            "description": "A single allowed value. functionally equivalent to an "
            "'enum' with a single value.",
        },
    )

    # Keywords for Numeric Instances (number and integer)
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-num
    minimum: float | None = field(
        default=None,
        metadata={
            "description": "The inclusive minimum allowed value.",
            "aliases": ["min", "ge"],
        },
    )
    maximum: float | None = field(
        default=None,
        metadata={
            "description": "The inclusive maximum allowed value.",
            "aliases": ["max", "le"],
        },
    )
    exclusive_minimum: float | None = field(
        default=None,
        metadata={
            "description": "The exclusive minimum allowed value.",
            "aliases": ["exclusiveMinimum", "gt"],
        },
    )
    exclusive_maximum: float | None = field(
        default=None,
        metadata={
            "description": "The exclusive maximum allowed value.",
            "aliases": ["exclusiveMaximum", "lt"],
        },
    )
    multiple_of: float | None = field(
        default=None,
        metadata={
            "description": "The allowed step size. Value is valid if (value / multiple_"
            "of) is an integer.",
            "aliases": ["multipleOf", "step"],
        },
    )
    # not in json schema, for Decimal types.  Also in pydantic.
    decimal_places: int | None = field(
        default=None,
        metadata={
            "descripion": "Maximum number of digits within the decimal. It does "
            "not include trailing decimal zeroes."
        },
    )

    # Keywords for String Instances
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-str
    min_length: int | None = field(
        default=None,
        metadata={
            "description": "The minimum allowed length. Must be >= 0.",
            "aliases": ["minLength"],
        },
    )
    max_length: int | None = field(
        default=None,
        metadata={
            "description": "The maximum allowed length. Must be >= 0.",
            "aliases": ["maxLength"],
        },
    )
    pattern: str | None = field(
        default=None,
        metadata={
            "description": "A regex pattern for the value.",
            "aliases": ["regex", "filter"],  # regex in pydantic, filter for FileEdit
        },
    )
    # NOTE: format is listed in this section, but needn't strictly apply to strings.
    format: JsonStringFormats | None = field(
        default=None, metadata={"description": "The format of the field."}
    )

    # Keywords for Sequence (Array) Instances
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-arr
    min_items: int | None = field(
        default=None,
        metadata={
            "description": "The (inclusive) minimum allowed number of items. "
            "Must be >= 0",
            # min_length/min_inclusive are from annotated_types
            "aliases": ["minItems", "min_length", "min_inclusive"],
        },
    )
    max_items: int | None = field(
        default=None,
        metadata={
            "description": "The (inclusive) maximum allowed number of items. "
            "Must be >= 0",
            "aliases": ["maxItems", "max_length"],  # max_length in annotated_types
        },
    )
    unique_items: bool | None = field(
        default=None,
        metadata={
            "description": "Whether the items in the list must be unique.",
            "aliases": ["uniqueItems"],
        },
    )

    # # Keywords for Mapping (Object) Instances
    # # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-obj  # noqa
    # max_properties: int | None = field(
    #     default=None,
    #     metadata=dict(description="The maximum allowed number of keys. Must be >= 0.")
    # )
    # min_properties: int | None = field(
    #     default=None,
    #     metadata=dict(description="The minimum allowed number of keys. Must be >= 0.")
    # )
    # required: list[str] | None = field(
    #     default=None,
    #     metadata=dict(
    #         description="A list of required keys that must be present in a mapping/object." # noqa
    #     ),
    # )

    read_only: bool | None = field(
        default=None,
        metadata={
            "description": "Whether the field is read-only. If True, the value of the "
            "instance is managed exclusively by the owning authority, and attempts by "
            "an application to modify the value of this property are expected to be "
            "ignored or rejected by that owning authority"
        },
    )

    # UI Specific
    widget: str | None = field(
        default=None,
        metadata={
            "description": "The name of the widget to use for this field. "
            "If not provided, the widget will be inferred from the type annotation."
        },
    )
    disabled: bool | None = field(
        default=None,
        metadata={
            "description": "Whether the widget should be disabled. Marking a field as "
            "read-only will render it greyed out, but its text value will be "
            "selectable. Disabling it will prevent its value to be selected at all."
        },
    )
    enum_disabled: list[T] | None = field(
        default=None,
        metadata={
            "description": "A list of values that should be disabled in a combobox "
            "widget."
        },
    )
    help: str | None = field(
        default=None,
        metadata={
            "description": "text next to a field to guide the end user filling it."
        },
    )
    placeholder: str | None = field(
        default=None,
        metadata={
            "description": "A placeholder string to display when the field is empty."
        },
    )
    visible: bool | None = field(
        default=None,
        metadata={
            "description": "Whether the field should be visible in the GUI. "
            "This is useful for hiding fields that are only used for validation."
        },
    )
    orientation: Literal["horizontal", "vertical"] | None = field(
        default=None,
        metadata={"description": "Orientation of the widget, for things like sliders."},
    )

    _native_field: Any | None = field(
        default=None,
        compare=False,
        hash=False,
        repr=False,
        metadata={
            "description": "Internal use only. If this field is derived from a native "
            "dataclasses.Field, or attrs.Attribute, or pydantic.fields.ModelField this "
            "will be a reference to that object."
        },
    )
    _original_annotation: Any | None = field(
        default=None,
        compare=False,
        hash=False,
        repr=False,
        metadata={
            "description": "Internal use only. If this field is derived from a "
            "typing.Annotated[...] annotation, this will be a reference to the origin "
            "annotation."
        },
    )

    def get_default(self) -> T | None:
        """Return the default value for this field."""
        return (
            self.default  # TODO: deepcopy mutable defaults?
            if self.default_factory is None
            else self.default_factory()
        )

    def asdict(self, include_unset: bool = True) -> dict[str, Any]:
        """Return the field as a dictionary.

        If `include_unset` is `False`, only fields that have been set will be included.
        """
        d = dc.asdict(self)
        if not include_unset:
            d = {
                k: v
                for k, v in d.items()
                if (v is not Undefined if k in ("default", "const") else v is not None)
            }
        return d

    def replace(self, **kwargs: Any) -> UiField:
        """Return a new Field with the given values replaced."""
        return dc.replace(self, **kwargs)

    @property
    def resolved_type(self) -> Any:
        """Return field type, resolving any forward references.

        Note that this will also return the origin type for Annotated types.
        """
        from magicgui._type_resolution import _try_cached_resolve

        return _try_cached_resolve(self.type)

    @property
    def is_annotated_type(self) -> bool:
        """Whether the field is an Annotated type."""
        return get_origin(self.type) is Annotated

    def parse_annotated(self) -> UiField[T]:
        """Extract info from Annotated type if present, and return new field.

        If self.type is not an Annotated type, return self.
        """
        if not self.is_annotated_type:
            return self

        kwargs = _uikwargs_from_annotated_type(self.type)

        if (
            self.default is not Undefined
            and kwargs.get("default", Undefined) is not Undefined
        ):
            warnings.warn(
                "Cannot set default value in both type annotation and field. Overriding"
                f" default {kwargs['default']} with {self.default} in field "
                f"{self.name!r}",
                stacklevel=2,
            )
            kwargs.pop("default", None)
        if self.name is not None and kwargs.get("name") is not None:
            warnings.warn(
                "Cannot set name in both type annotation and field. Overriding"
                f" name {kwargs['name']!r} with {self.name!r} in field {self.name!r}",
                stacklevel=2,
            )
            kwargs.pop("name", None)
        return dc.replace(self, **kwargs)

    def create_widget(self, value: T | _Undefined = Undefined) -> ValueWidget[T]:
        """Create a new Widget for this field."""
        from magicgui.type_map import get_widget_class

        # TODO: this should be cached in some way
        # Map uifield names to widget kwargs
        # FIXME: this part needs a lot of work.
        # This is the biggest challenge for integrating this new UiField idea
        # (which tries to map nicely to existing schemas like JSON Schema)
        # with the rest of the codebase, which used less "general" naming schemes.
        _name_map = {
            "name": "name",
            "visible": "visible",
            "nullable": "nullable",
            "orientation": "orientation",
            "type": "annotation",
            "enum": "choices",
            "title": "label",
            "description": "tooltip",
            "maximum": "max",
            "minimum": "min",
            # "title": "text",  # PushButton only
            # "exclusive_maximum": "stop",  # RangeEdit only
            # "minimum": "start", # RangeEdit only
            "multiple_of": "step",
            "widget": "widget_type",
        }

        d = (
            self.parse_annotated()
            .replace(_native_field=None)
            .asdict(include_unset=False)
        )
        opts = {_name_map[k]: v for k, v in d.items() if k in _name_map}
        if "disabled" in d:
            opts["enabled"] = not d["disabled"]

        # TODO: very hacky... but we don't have the concept of exclusive min/max
        # for float values.
        if "exclusive_maximum" in d:
            m = 1 if d.get("type") is int else 0.00000000001
            opts["max"] = d["exclusive_maximum"] - m
        if "exclusive_minimum" in d:
            m = 1 if d.get("type") is int else 0.00000000001
            opts["min"] = d["exclusive_minimum"] + m

        value = value if value is not Undefined else self.get_default()  # type: ignore
        cls, kwargs = get_widget_class(value=value, annotation=self.type, options=opts)
        return cls(**kwargs)  # type: ignore


_UI_FIELD_NAMES: set[str] = set()
_UI_FIELD_ALIASES: dict[str, str] = {}

# gather up all the aliases for the UiField fields
# so we can use them in _rename_aliases
for field_info in dc.fields(UiField):
    _UI_FIELD_NAMES.add(field_info.name)
    for alias in field_info.metadata.get("aliases", []):
        _UI_FIELD_ALIASES[alias] = field_info.name


def _rename_aliases(input: dict[str, Any]) -> dict[str, Any]:
    """Rename any aliases in the input dict to their accepted names."""
    return {_UI_FIELD_ALIASES.get(k, k): v for k, v in input.items()}


def _uikwargs_from_annotated_type(hint: Any) -> dict[str, Any]:
    """Convert an Annotated type to a dict of UiField kwargs."""
    # hint must be an Annotated[...] type

    annotated_types = sys.modules.get("annotated_types")
    base_metas: list[BaseMetadata] = []

    origin, *metadata = get_args(hint)
    kwargs = {}
    for item in metadata:
        if isinstance(item, UiField):
            kwargs.update(item.asdict(include_unset=False))
        elif annotated_types is not None:
            # annotated_types >= 0.3.0 is supported
            if isinstance(item, annotated_types.BaseMetadata):
                base_metas.append(item)
            elif isinstance(item, annotated_types.GroupedMetadata):
                base_metas.extend(item)
        # TODO: support pydantic.fields.FieldInfo?
        # TODO: support re.Pattern?

    if base_metas:
        _annotated_kwargs = {}
        for i in base_metas:
            _annotated_kwargs.update(dc.asdict(i))
        if "max_exclusive" in _annotated_kwargs:
            _annotated_kwargs["max_items"] = _annotated_kwargs.pop("max_exclusive") - 1
        kwargs.update(_rename_aliases(_annotated_kwargs))

    kwargs.update({"type": origin, "_original_annotation": hint})
    return kwargs


def _uifield_from_dataclass(field: dc.Field) -> UiField:
    """Create a UiField from a dataclass field."""
    default = field.default if field.default is not dc.MISSING else Undefined
    dfactory = (
        field.default_factory if field.default_factory is not dc.MISSING else None
    )
    extra = {k: v for k, v in field.metadata.items() if k in _UI_FIELD_NAMES}

    return UiField(
        name=field.name,
        type=field.type,
        default=default,
        default_factory=dfactory,
        _native_field=field,
        **extra,
    )


def _uifield_from_attrs(field: Attribute) -> UiField:
    """Create a UiField from an attrs field."""
    from attrs import NOTHING, Factory

    default = field.default if field.default is not NOTHING else Undefined
    default_factory = None
    if isinstance(default, Factory):
        default_factory = default.factory
        default = Undefined

    extra = {k: v for k, v in field.metadata.items() if k in _UI_FIELD_NAMES}

    return UiField(
        name=field.name,
        type=field.type,
        default=default,
        default_factory=default_factory,
        _native_field=field,
        **extra,
    )


def _uifield_from_pydantic1(model_field: ModelField) -> UiField:
    """Create a UiField from a pydantic ModelField."""
    from pydantic.fields import SHAPE_SINGLETON
    from pydantic.fields import Undefined as PydanticUndefined

    finfo = model_field.field_info

    _extra_dict = finfo.extra.copy()
    # backport from pydantic2
    if "json_schema_extra" in _extra_dict:
        _extra_dict.update(_extra_dict.pop("json_schema_extra"))

    extra = {k: v for k, v in _extra_dict.items() if k in _UI_FIELD_NAMES}
    const = finfo.const if finfo.const not in (None, PydanticUndefined) else Undefined
    default = (
        Undefined if finfo.default in (PydanticUndefined, Ellipsis) else finfo.default
    )

    nullable = None
    if model_field.allow_none and (
        model_field.shape != SHAPE_SINGLETON or not model_field.sub_fields
    ):
        nullable = True

    return UiField(
        name=model_field.name,
        title=finfo.title,
        description=finfo.description,
        default=default,
        default_factory=model_field.default_factory,
        type=model_field.outer_type_,
        nullable=nullable,
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
        _native_field=model_field,
        **extra,
    )


def _uifield_from_pydantic2(finfo: FieldInfo, name: str) -> UiField:
    """Create a UiField from a pydantic ModelField."""
    import annotated_types as at
    from pydantic_core import PydanticUndefined

    if isinstance(finfo.json_schema_extra, dict):
        extra = {
            k: v for k, v in finfo.json_schema_extra.items() if k in _UI_FIELD_NAMES
        }
    else:
        extra = {}
    default = (
        Undefined if finfo.default in (PydanticUndefined, Ellipsis) else finfo.default
    )

    nullable = None
    if get_origin(finfo.annotation) is Union and any(
        i for i in get_args(finfo.annotation) if i is type(None)
    ):
        nullable = True

    restrictions: dict = {}
    for meta in finfo.metadata:
        if isinstance(meta, at.Ge):
            restrictions["minimum"] = meta.ge
        elif isinstance(meta, at.Gt):
            restrictions["exclusive_minimum"] = meta.gt
        elif isinstance(meta, at.Le):
            restrictions["maximum"] = meta.le
        elif isinstance(meta, at.Lt):
            restrictions["exclusive_maximum"] = meta.lt
        elif isinstance(meta, at.MultipleOf):
            restrictions["multiple_of"] = meta.multiple_of
        elif isinstance(meta, at.MinLen):
            restrictions["min_length"] = meta.min_length
        elif isinstance(meta, at.MaxLen):
            restrictions["max_length"] = meta.max_length
        elif hasattr(meta, "__dict__"):
            # PydanticGeneralMetadata
            restrictions["pattern"] = meta.__dict__.get("pattern")

    return UiField(
        name=name,
        title=finfo.title,
        description=finfo.description,
        default=default,
        default_factory=finfo.default_factory,
        type=finfo.annotation,
        nullable=nullable,
        # const=const,
        **restrictions,
        # format=finfo.format,
        _native_field=finfo,
        **extra,
    )


# TODO:
class _ContainerFields:
    autofocus: str | None = field(
        default=None,
        metadata={"description": "Name of a field that should be autofocused on."},
    )
    labels: list[str] | bool | None = field(
        default=None,
        metadata={
            "description": "If True, all fields will be labeled. If False, no fields "
            "will be labeled. If a list, only the fields in the list will be labeled."
        },
    )


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
            return _get_pydantic_model(cls.__pydantic_model__)
    return None


def _get_function_defaults(func: FunctionType) -> dict[str, Any]:
    """Return a dict of the default values for a function's parameters."""
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


def _ui_fields_from_annotation(cls: type) -> Iterator[UiField]:
    """Iterate UiFields extracted from object __annotations__."""
    # fallback for typed dict, named tuples, & functions

    annotations: dict = getattr(cls, "__annotations__", {})
    if not annotations and isinstance(annotations, dict):  # pragma: no cover
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


def _iter_ui_fields(object: Any) -> Iterator[UiField]:
    # check if it's a pydantic model
    model = _get_pydantic_model(object)
    if model is not None:
        if hasattr(model, "model_fields"):
            for name, field_info in model.model_fields.items():
                yield _uifield_from_pydantic2(field_info, name)
        else:
            for pf in model.__fields__.values():
                yield _uifield_from_pydantic1(pf)
        return

    if hasattr(object, "__pydantic_fields__"):
        # pydantic2 style dataclass
        for name, field_info in object.__pydantic_fields__.items():
            yield _uifield_from_pydantic2(field_info, name)
        return

    # check if it's a (non-pydantic) dataclass
    if dc.is_dataclass(object):
        for df in dc.fields(object):
            yield _uifield_from_dataclass(df)
        return

    # check if it's an attrs class
    if _is_attrs_model(object):
        for af in object.__attrs_attrs__:
            yield _uifield_from_attrs(af)
        return

    # fallback to looking at __annotations__ (named tuple, typed dict, function)
    if hasattr(object, "__annotations__"):
        yield from _ui_fields_from_annotation(object)
        return

    raise TypeError(
        f"{object} is not a dataclass, attrs, or pydantic, model"
    )  # pragma: no cover


@lru_cache(maxsize=None)
def _cached_iter_ui_fields(cls: type) -> tuple[UiField, ...]:
    return tuple(_iter_ui_fields(cls))


def get_ui_fields(cls_or_instance: object) -> tuple[UiField, ...]:
    """Derive UIFields from an object.

    Parameters
    ----------
    cls_or_instance : Any
        Object to extract fields from.  Could be a dataclass or dataclass instance,
        an attrs class or instance, a pydantic model or instance, a named tuple,
        typed dict, or a function.
    """
    try:
        if isinstance(cls_or_instance, (type, FunctionType)):
            return _cached_iter_ui_fields(cls_or_instance)
        return _cached_iter_ui_fields(type(cls_or_instance))  # type: ignore
    except TypeError:
        return tuple(_iter_ui_fields(cls_or_instance))


def _uifields_to_container(
    ui_fields: Iterable[UiField],
    values: Mapping[str, Any] | None = None,
    *,
    container_kwargs: Mapping | None = None,
) -> ContainerWidget[ValueWidget]:
    """Create a container widget from a sequence of UiFields.

    This function is the heart of build_widget.

    Parameters
    ----------
    ui_fields : Iterable[UiField]
        A sequence of UiFields to use to create the container.
    values : Mapping[str, Any], optional
        A mapping of field name to values to use to initialize each widget the
        container, by default None.
    container_kwargs : Mapping, optional
        A mapping of keyword arguments to pass to the container constructor,
        by default None.

    Returns
    -------
    ContainerWidget[ValueWidget]
        A container widget with a widget for each UiField.
    """
    from magicgui import widgets

    container = widgets.Container(
        widgets=[field.create_widget() for field in ui_fields],
        **(container_kwargs or {}),
    )
    if values is not None:
        container.update(values)
    return container


def _get_values(obj: Any) -> dict | None:
    """Return a dict of values from an object.

    The object can be a dataclass, attrs, pydantic object or named tuple.
    """
    if isinstance(obj, dict):
        return obj

    # named tuple
    if isinstance(obj, tuple) and hasattr(obj, "_asdict"):
        return cast(dict, obj._asdict())

    # dataclass
    if dc.is_dataclass(type(obj)):
        return dc.asdict(obj)

    # attrs
    attr = sys.modules.get("attr")
    if attr is not None and attr.has(obj):
        return cast(dict, attr.asdict(obj))

    # pydantic models
    if hasattr(obj, "model_dump"):
        return cast(dict, obj.model_dump())
    elif hasattr(obj, "dict"):
        return cast(dict, obj.dict())

    return None


# TODO: unify this with magicgui
def build_widget(cls_or_instance: Any) -> ContainerWidget[ValueWidget]:
    """Build a magicgui widget from a dataclass, attrs, pydantic, or function."""
    values = None if isinstance(cls_or_instance, type) else _get_values(cls_or_instance)
    return _uifields_to_container(get_ui_fields(cls_or_instance), values=values)
