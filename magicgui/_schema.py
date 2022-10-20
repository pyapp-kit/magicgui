from __future__ import annotations

import dataclasses as dc
import sys
import warnings
from dataclasses import dataclass, field
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterator, Sequence, Union

from typing_extensions import Annotated, Literal, TypeGuard, get_args, get_origin

from .types import JsonStringFormats, Undefined

if TYPE_CHECKING:
    from typing import Protocol
    from .widgets._bases import ValueWidget

    import attrs
    import pydantic
    from annotated_types import BaseMetadata
    from attrs import Attribute
    from pydantic.fields import ModelField

    class HasAttrs(Protocol):
        """Protocol for objects that have an ``attrs`` attribute."""

        __attrs_attrs__: tuple[attrs.Attribute, ...]


_dc_kwargs = {"frozen": True}
if sys.version_info >= (3, 10):
    _dc_kwargs["slots"] = True


@dataclass(**_dc_kwargs)
class UiField:
    """Metadata about a specific widget in a GUI."""

    def __post_init__(self):
        """Coerce Optional[...] to nullable and remove it from the type."""
        if get_origin(self.type) is Union:
            args = get_args(self.type)
            nonnull = tuple(a for a in args if a is not type(None))  # noqa: E721
            if len(nonnull) < len(args):
                object.__setattr__(self, "type", Union[nonnull])
                object.__setattr__(self, "nullable", True)

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
            "the `name` will be used.",
            aliases=["label", "text", "button_text"],
        ),
    )
    description: str | None = field(
        default=None,
        metadata=dict(description="A description of the field.", aliases=["tooltip"]),
    )
    default: Any = field(
        default=Undefined,
        metadata=dict(
            description="The default value for the field.", aliases=["value"]
        ),
    )
    # NOTE: this does not have an analog in JSON Schema
    default_factory: Callable[[], Any] | None = field(
        default=None,
        metadata=dict(
            description="A callable that returns the default value of the field."
        ),
    )
    # NOTE: this does not have an analog in JSON Schema
    nullable: bool | None = field(
        default=None,
        metadata=dict(
            description="Whether the field is nullable. In JSON, this is equivalent to "
            "`type: [<type>, 'null']`"
        ),
    )

    # Keywords for Any Instance Type
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-any
    type: Any = field(
        default=None, metadata=dict(description="The type annotation of the field.")
    )
    enum: list[Any] | None = field(
        default=None,
        metadata=dict(description="A list of allowed values.", aliases=["choices"]),
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
        default=None,
        metadata=dict(
            description="The inclusive minimum allowed value.", aliases=["min", "ge"]
        ),
    )
    maximum: float | None = field(
        default=None,
        metadata=dict(
            description="The inclusive maximum allowed value.",
            aliases=["max", "le"],
        ),
    )
    exclusive_minimum: float | None = field(
        default=None,
        metadata=dict(
            description="The exclusive minimum allowed value.",
            aliases=["exclusiveMinimum", "gt"],
        ),
    )
    exclusive_maximum: float | None = field(
        default=None,
        metadata=dict(
            description="The exclusive maximum allowed value.",
            aliases=["exclusiveMaximum", "lt"],
        ),
    )
    multiple_of: float | None = field(
        default=None,
        metadata=dict(
            description="The allowed step size. Value is valid if (value / multiple_of)"
            " is an integer.",
            aliases=["multipleOf", "step"],
        ),
    )
    # not in json schema, for Decimal types.  Also in pydantic.
    decimal_places: int | None = field(
        default=None,
        metadata=dict(
            descripion="Maximum number of digits within the decimal. It does "
            "not include trailing decimal zeroes."
        ),
    )

    # Keywords for String Instances
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-str
    min_length: int | None = field(
        default=None,
        metadata=dict(
            description="The minimum allowed length. Must be >= 0.",
            aliases=["minLength"],
        ),
    )
    max_length: int | None = field(
        default=None,
        metadata=dict(
            description="The maximum allowed length. Must be >= 0.",
            aliases=["maxLength"],
        ),
    )
    pattern: str | None = field(
        default=None,
        metadata=dict(
            description="A regex pattern for the value.",
            aliases=["regex", "filter"],  # regex in pydantic, filter for FileEdit
        ),
    )
    # NOTE: format is listed in this section, but needn't strictly apply to strings.
    format: JsonStringFormats | None = field(
        default=None, metadata=dict(description="The format of the field.")
    )

    # Keywords for Sequence (Array) Instances
    # https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-arr
    min_items: int | None = field(
        default=None,
        metadata=dict(
            description="The (inclusive) minimum allowed number of items. Must be >= 0",
            # min_length/min_inclusive are from annotated_types
            aliases=["minItems", "min_length", "min_inclusive"],
        ),
    )
    max_items: int | None = field(
        default=None,
        metadata=dict(
            description="The (inclusive) maximum allowed number of items. Must be >= 0",
            aliases=["maxItems", "max_length"],  # max_length in annotated_types
        ),
    )
    unique_items: bool | None = field(
        default=None,
        metadata=dict(
            description="Whether the items in the list must be unique.",
            aliases=["uniqueItems"],
        ),
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
        metadata=dict(
            description="Whether the field is read-only. If True, the value of the "
            "instance is managed exclusively by the owning authority, and attempts by "
            "an application to modify the value of this property are expected to be "
            "ignored or rejected by that owning authority"
        ),
    )

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

    _native_field: Any | None = field(
        default=None,
        compare=False,
        hash=False,
        repr=False,
        metadata=dict(
            description="Internal use only. If this field is derived from a native "
            "dataclasses.Field, or attrs.Attribute, or pydantic.fields.ModelField this "
            "will be a reference to that object."
        ),
    )
    _original_annotation: Any | None = field(
        default=None,
        compare=False,
        hash=False,
        repr=False,
        metadata=dict(
            description="Internal use only. If this field is derived from a "
            "typing.Annotated[...] annotation, this will be a reference to the origin "
            "annotation."
        ),
    )

    def create(self) -> ValueWidget:
        from .type_map import get_widget_class

        widget_class, _widget_kwargs = get_widget_class(
            annotation=self.type, options=...
        )
        widget_kwargs = dict(_widget_kwargs)


    def get_default(self) -> Any:
        """Return the default value for this field."""
        return (
            self.default  # TODO: deepcopy mutable defaults?
            if self.default_factory is None
            else self.default_factory()
        )

    def dict(self, include_unset: bool = True) -> dict[str, Any]:
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

    @property
    def resolved_type(self) -> Any:
        """Return field type, resolving any forward references.

        Note that this will also return the origin type for Annotated types.
        """
        from ._type_resolution import _try_cached_resolve

        return _try_cached_resolve(self.type)

    @property
    def is_annotated_type(self) -> bool:
        """Whether the field is an Annotated type."""
        return get_origin(self.type) is Annotated

    def parse_annotated(self) -> UiField:
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
                f"{self.name!r}"
            )
            kwargs.pop("default", None)
        if self.name is not None and kwargs.get("name") is not None:
            warnings.warn(
                "Cannot set name in both type annotation and field. Overriding"
                f" name {kwargs['name']!r} with {self.name!r} in field {self.name!r}"
            )
            kwargs.pop("name", None)
        return dc.replace(self, **kwargs)


_UI_FIELD_NAMES: set[str] = set()
_UI_FIELD_ALIASES: Dict[str, str] = {}

for field_info in dc.fields(UiField):
    _UI_FIELD_NAMES.add(field_info.name)
    for alias in field_info.metadata.get("aliases", []):
        _UI_FIELD_ALIASES[alias] = field_info.name


def _rename_aliases(input: dict[str, Any]) -> dict[str, Any]:
    """Rename any aliases in the input dict."""
    return {_UI_FIELD_ALIASES.get(k, k): v for k, v in input.items()}


def _uikwargs_from_annotated_type(hint: Any) -> Dict[str, Any]:
    # hint must be an Annotated[...] type

    annotated_types = sys.modules.get("annotated_types")
    base_metas: list[BaseMetadata] = []

    origin, *metadata = get_args(hint)
    kwargs = {}
    for item in metadata:
        if isinstance(item, UiField):
            kwargs.update(item.dict(include_unset=False))
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


def _uifield_from_pydantic(model_field: ModelField) -> UiField:
    from pydantic.fields import SHAPE_SINGLETON
    from pydantic.fields import Undefined as PydanticUndefined

    finfo = model_field.field_info

    extra = {k: v for k, v in finfo.extra.items() if k in _UI_FIELD_NAMES}
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


def _ui_fields_from_annotation(cls) -> Iterator[UiField]:
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


def iter_ui_fields(object: Any) -> Iterator[UiField]:
    """Iterate UiFields extracted from object.

    Parameters
    ----------
    object : Any
        Object to extract fields from.  Could be a dataclass or dataclass instance,
        an attrs class or instance, a pydantic model or instance, a named tuple,
        typed dict, or a function.
    """
    # check if it's a (non-pydantic) dataclass
    if dc.is_dataclass(object) and not hasattr(object, "__pydantic_model__"):
        for df in dc.fields(object):
            yield _uifield_from_dataclass(df)
        return

    # check if it's an attrs class
    if _is_attrs_model(object):
        for af in object.__attrs_attrs__:
            yield _uifield_from_attrs(af)
        return

    # check if it's a pydantic model
    model = _get_pydantic_model(object)
    if model is not None:
        for pf in model.__fields__.values():
            yield _uifield_from_pydantic(pf)
        return

    # fallback to looking at __annotations__ (named tuple, typed dict, function)
    if hasattr(object, "__annotations__"):
        yield from _ui_fields_from_annotation(object)
        return

    raise TypeError(
        f"{object} is not a dataclass, attrs, or pydantic, model"
    )  # pragma: no cover


def _build_fields():

    if instance is not None:
        _values = instance.dict()
    else:
        _values = {
            k: f.get_default() for k, f in cls.__fields__.items() if not f.required
        }

    if values:
        _values.update(values)

    wdg = _build_widget(cls.__ui_info__, _values)
    if instance is not None:
        config = getattr(instance, "__config__", None)
        if bind_changes is None:
            bind_changes = not getattr(config, "frozen", False) and getattr(
                config, "allow_mutation", True
            )
        if bind_changes:
            bind_gui_changes_to_model(gui=wdg, model=instance)
        else:
            breakpoint()
    return wdg


def _build_widget(
    ui_info: Sequence[UiField],
    values: Union[Mapping[str, Any], None] = None,
) -> ContainerWidget[ValueWidget]:
    """Build a widget for a mapping of field names to UI metadata.

    Parameters
    ----------
    ui_info : Dict[str, ResolvedUIMetadata]
        keys are field names, values are ResolvedUIMetadata instances.
        (a named tuple containing `(widget_class, kwargs)`)
    values : Union[Mapping[str, Any], None], optional
        Optionally values to initialize the widget, by default None

    Returns
    -------
    ValueWidgetContainer
        A magicgui Container instance with widgets representing each field.
    """
    from magicgui import widgets

    values = values or {}

    wdgs = []
    for ui_metadata in ui_info:
        new_widget = ui_metadata.create()

        # field_name = ui_metadata.name
        # wdg_kwargs = dict(ui_metadata.options)
        # wdg_kwargs.setdefault("name", field_name)
        # value = values.get(field_name, Undefined)
        # if value is not Undefined:
        #     wdg_kwargs["value"] = value
        # new_widget = ui_metadata.widget(**wdg_kwargs)
        # wdgs.append(new_widget)

    return widgets.Container(widgets=wdgs)
