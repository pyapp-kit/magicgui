import contextlib
import types
import weakref
from collections import OrderedDict, defaultdict, deque
from copy import copy
from dataclasses import dataclass, field, fields, replace
from typing import (
    Annotated,
    Any,
    Callable,
    Dict,
    ForwardRef,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
)

from typing_extensions import Literal

from magicgui._type_resolution import resolve_single_type
from magicgui.types import JsonStringFormats, Undefined, WidgetRef, _Undefined
from magicgui.widgets._bases.value_widget import ValueWidget


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
    # TODO: can we remove this?
    button_text: Optional[str] = field(
        default=None,
        metadata=dict(description="The text of a button", aliases=["text"]),
    )
    # mode: str | FileDialogMode


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
    pattern: Optional[str] = field(
        default=None,
        metadata=dict(
            description="Regular expression pattern. For file dialogs, this is used "
            "to filter the files shown, and will be interpreted as a glob pattern. "
            "For other strings, it is a regex pattern.",
            aliases=["regex", "filter"],
        ),
    )
    format: Optional[JsonStringFormats] = field(
        default=None,
        metadata=dict(
            description="Allows for basic semantic identification of certain kinds of "
            "string values that are commonly used. This is primarily used for "
            "JSON Schema conversion; python types should be preferred when possible.",
        ),
    )


@dataclass(frozen=True)
class ArrayContraints:
    min_items: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Minimum length of the list. Must be a non-negative number.",
            aliases=["minItems"],
        ),
    )
    max_items: Optional[int] = field(
        default=None,
        metadata=dict(
            description="Maximum length of the list. Must be a non-negative number.",
            aliases=["maxItems"],
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
    orientation: Optional[Literal["horizontal", "vertical"]] = field(
        default=None,
        metadata=dict(description="Orientation of the widget."),
    )
    # gui_only: bool
    # tooltip: str  # alias for FieldInfo.description?


@dataclass(frozen=True)
class ContainerOptions:
    layout: str  # for things like containers


@dataclass(frozen=True)
class UiFieldInfo(
    WidgetConstraints,
    ArrayContraints,
    StringContraints,
    NumericContraints,
    FieldInfo,
    ValueConstraints,
):
    extra: dict = field(
        default_factory=dict,
        metadata=dict(description="Extra info passed to the UiField constructor"),
    )


FIELDS: Set[str] = set()
ALIASES: Dict[str, str] = {}

for field_info in fields(UiFieldInfo):
    FIELDS.add(field_info.name)
    for alias in field_info.metadata.get("aliases", []):
        ALIASES[alias] = field_info.name


def UiField(
    *,
    default: Any = Undefined,
    default_factory: Optional[Callable[[], Any]] = None,
    const: bool = False,
    enum: Optional[List[Any]] = None,
    bind: Union[Callable[[ValueWidget], Any], Any, None] = None,
    #
    title: Optional[str] = None,
    description: Optional[str] = None,
    button_text: Optional[str] = None,
    #
    multiple_of: Optional[float] = None,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    exclusive_minimum: Optional[float] = None,
    exclusive_maximum: Optional[float] = None,
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    #
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    pattern: Optional[str] = None,
    format: Optional[JsonStringFormats] = None,
    #
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: Optional[bool] = None,
    #
    widget_type: Optional[WidgetRef] = None,
    visible: bool = True,
    enabled: bool = True,
    orientation: Optional[Literal["horizontal", "vertical"]] = None,
    **extra,
) -> UiFieldInfo:

    _extra = dict(extra)
    for key in list(_extra):
        if key not in FIELDS:
            if key in ALIASES:
                # if locals()[ALIASES[key]] is None:  # which takes precendence ?
                locals()[ALIASES[key]] = _extra.pop(key)
            elif key == "allow_multiple":
                _extra.pop(key)
                widget_type = "Select"
                # TODO: add a warning
            elif key in ("options", "readout", "tracking", "mode"):
                # TODO
                # _extra.pop(key)
                ...
            else:
                raise ValueError(f"{key} is not a valid field")

    return UiFieldInfo(
        default=default,
        default_factory=default_factory,
        const=const,
        enum=enum,
        bind=bind,
        #
        title=title,
        description=description,
        button_text=button_text,
        #
        multiple_of=multiple_of,
        minimum=minimum,
        maximum=maximum,
        exclusive_minimum=exclusive_minimum,
        exclusive_maximum=exclusive_maximum,
        max_digits=max_digits,
        decimal_places=decimal_places,
        #
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        format=format,
        #
        min_items=min_items,
        max_items=max_items,
        unique_items=unique_items,
        #
        widget_type=widget_type,
        visible=visible,
        enabled=enabled,
        orientation=orientation,
        extra=_extra,
    )


class GUIField:
    __slots__ = (
        "name",
        "type_",
        "default",
        "default_factory",
        "required",
        "field_info",
    )

    def __init__(
        self,
        *,
        name: str,
        type_: Type[Any],
        default: Any = None,
        default_factory: Optional[Callable[[], Any]] = None,
        required: Union[bool, _Undefined] = Undefined,
        field_info: Optional[UiFieldInfo] = None,
    ) -> None:
        self.name = name
        self.type_ = type_
        self.default = default
        self.default_factory = default_factory
        self.required = required
        self.field_info: UiFieldInfo = field_info or UiFieldInfo(default=default)

    def __repr__(self):
        name = self.__class__.__name__
        args = ((k, getattr(self, k)) for k in self.__slots__)
        args = ", ".join(f"{k}={v}" for k, v in args)
        return f"{name}({args})>"

    def get_default(self) -> Any:
        return (
            _smart_deepcopy(self.default)
            if self.default_factory is None
            else self.default_factory()
        )

    @classmethod
    def infer(cls, *, name: str, value: Any, annotation: Any) -> "GUIField":
        """Infer a `GUIField` from a variable name, annotation, and value

        ...as would be provided in either a function signature or a class definition

            def foo(name: annotation = value): ...

            class Foo:
                name: annotation = value

            class Bar:
                name: int = UiField(default=42, description="the answer")

            class Bar:
                name: Annotated[int, UiField(description="the answer")] = 42

        Parameters
        ----------
        name : str
            name of the variable
        value : Any
            default value of the variable, (might be an instance of `UiFieldInfo`)
        annotation : Any
            type annotation of the variable, (might be an instance of `typing.Annotated`
            with a UiFieldInfo as the annotation)
        """

        field_info, value = cls._get_field_info(name, annotation, value)
        required: Union[bool, _Undefined] = Undefined
        if value is Ellipsis:
            required = True
            value = None
        elif value is not Undefined:
            required = False

        if annotation in (Undefined, None) and value is not Undefined:
            type_ = type(value)
        elif isinstance(annotation, (str, ForwardRef)):
            try:
                type_ = resolve_single_type(annotation)
            except (NameError, ImportError) as e:
                raise type(e)(f"Magicgui could not resolve {annotation}: {e}") from e
        else:
            type_ = annotation

        return cls(
            name=name,
            type_=type_,
            default=value,
            default_factory=field_info.default_factory,
            required=required,
            field_info=field_info,
        )

    @staticmethod
    def _get_field_info(
        field_name: str, annotation: Any, value: Any
    ) -> Tuple[UiFieldInfo, Any]:
        field_info: Optional[UiFieldInfo] = None
        if get_origin(annotation) is Annotated:
            field_infos: List[UiFieldInfo] = [
                arg for arg in get_args(annotation)[1:] if isinstance(arg, UiFieldInfo)
            ]
            if len(field_infos) > 1:
                raise ValueError(
                    f"cannot specify multiple `Annotated` `UiField`s for {field_name!r}"
                )

            field_info = field_infos[0] if field_infos else None
            if field_info is not None:
                field_info = copy(field_info)
                if field_info.default not in (Undefined, Ellipsis):
                    raise ValueError(
                        "`UiField` default cannot be set in `Annotated` "
                        f"for {field_name!r}"
                    )
                if value is not Undefined and value is not Ellipsis:
                    # check also `Required` because of `validate_arguments`
                    # that sets `...` as default value
                    field_info = replace(field_info, default=value)

        if isinstance(value, UiFieldInfo):
            if field_info is not None:
                raise ValueError(
                    "cannot specify `Annotated` and value `UiField`s together "
                    f"for {field_name!r}"
                )
            field_info = value
        elif field_info is None:
            field_info = UiFieldInfo(default=value)
        value = None if field_info.default_factory is not None else field_info.default
        return field_info, value

    # def build(self):
    # return self.widget_type(self.widget_kwargs)


# these are types that are returned unchanged by deepcopy
IMMUTABLE_NON_COLLECTIONS_TYPES: Set[Type] = {
    int,
    float,
    complex,
    str,
    bool,
    bytes,
    type,
    type(None),
    types.FunctionType,
    types.BuiltinFunctionType,
    types.LambdaType,
    weakref.ref,
    types.CodeType,
    types.ModuleType,
    type(NotImplemented),
    type(Ellipsis),
}

# these are types that if empty, might be copied with simple copy() instead of deepcopy()
BUILTIN_COLLECTIONS: Set[Type] = {
    list,
    set,
    tuple,
    frozenset,
    dict,
    OrderedDict,
    defaultdict,
    deque,
}

T = TypeVar("T")


def _smart_deepcopy(obj: T) -> T:
    """Return type as is for immutable built-in types

    Use obj.copy() for built-in empty collections
    Use copy.deepcopy() for non-empty collections and unknown objects
    """
    from copy import deepcopy

    obj_type = type(obj)
    if obj_type in IMMUTABLE_NON_COLLECTIONS_TYPES:
        return obj  # fastest case: obj is immutable
    with contextlib.suppress(TypeError, ValueError, RuntimeError):
        if obj_type in BUILTIN_COLLECTIONS and not obj:
            # faster way for empty collections, no need to copy its members
            return obj if isinstance(obj, tuple) else obj.copy()
    return deepcopy(obj)  # slowest way when we actually might need a deepcopy
