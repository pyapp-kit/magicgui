"""Functions in this module are responsible for mapping type annotations to widgets."""
from __future__ import annotations

import datetime
import inspect
import ipaddress
import pathlib
import types
import uuid
import warnings
from collections import defaultdict
from dataclasses import MISSING, Field
from enum import EnumMeta
from functools import lru_cache
from typing import (
    Any,
    Callable,
    DefaultDict,
    ForwardRef,
    Mapping,
    Type,
    TypeVar,
    cast,
    overload,
)

from pydantic import BaseConfig
from pydantic.errors import ConfigError
from pydantic.fields import (
    SHAPE_DEQUE,
    SHAPE_LIST,
    SHAPE_SEQUENCE,
    SHAPE_TUPLE,
    SHAPE_TUPLE_ELLIPSIS,
    ModelField,
    Undefined,
)
from typing_extensions import Literal

from magicgui import widgets
from magicgui.types import (
    PathLike,
    ReturnCallback,
    WidgetClass,
    WidgetOptions,
    WidgetRef,
)
from magicgui.widgets._protocols import WidgetProtocol, assert_protocol

__all__: list[str] = ["register_type", "get_widget_class"]


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""


class WidgetMeta:
    __slots__ = ("_widget_class", "widget_kwargs", "", "_resolved_class")
    _resolved_class: type[widgets.Widget]

    def __init__(
        self, widget_class: str | type[widgets.Widget], widget_kwargs: dict
    ) -> None:
        self._widget_class = widget_class
        self.widget_kwargs = widget_kwargs

    def _validate(self) -> None:
        _ = self.widget_class
        # check if key is a valid kwargs for the widget class

    @property
    def widget_class(self) -> type[widgets.Widget]:
        if self._resolved_class is None:
            from magicgui.widgets import Widget

            if isinstance(self._widget_class, Widget):
                self._resolved_class = self.__widget_class
            else:
                ...
            # self._resolved_class = resolve_widget_class(self.widget_class)
        return self._resolved_class


FieldType = ModelField


SEQUENCE_LIKE: set[int] = {
    SHAPE_LIST,
    SHAPE_TUPLE,
    SHAPE_TUPLE_ELLIPSIS,
    SHAPE_SEQUENCE,
    SHAPE_DEQUE,
}


_RETURN_CALLBACKS: DefaultDict[type, list[ReturnCallback]] = defaultdict(list)
_TYPE_DEFS: dict[type, WidgetMeta] = dict()


def _is_subclass(obj, superclass):
    """Safely check if obj is a subclass of superclass."""
    try:
        return issubclass(obj, superclass)
    except Exception:
        return False


_SIMPLE_ANNOTATIONS = {
    PathLike: widgets.FileEdit,
}

_SIMPLE_TYPES = {
    bool: widgets.CheckBox,
    int: widgets.SpinBox,
    float: widgets.FloatSpinBox,
    str: widgets.LineEdit,
    bytes: widgets.LineEdit,
    pathlib.Path: widgets.FileEdit,
    datetime.time: widgets.TimeEdit,
    datetime.timedelta: widgets.TimeEdit,
    datetime.date: widgets.DateEdit,
    datetime.datetime: widgets.DateTimeEdit,
    range: widgets.RangeEdit,
    slice: widgets.SliceEdit,
    list: widgets.ListEdit,
    tuple: widgets.TupleEdit,
    uuid.UUID: widgets.LineEdit,
    ipaddress.IPv4Address: widgets.LineEdit,
    ipaddress.IPv6Address: widgets.LineEdit,
    ipaddress.IPv4Network: widgets.LineEdit,
    ipaddress.IPv6Network: widgets.LineEdit,
}


def match_type(tw: FieldType) -> WidgetMeta | None:
    """Check simple type mappings."""
    _type = tw.outer_type_

    if _type in _SIMPLE_ANNOTATIONS:
        return WidgetMeta(_SIMPLE_ANNOTATIONS[_type], {})

    if _type is widgets.ProgressBar:
        return WidgetMeta(
            widgets.ProgressBar, {"bind": lambda widget: widget, "visible": True}
        )

    if _type in _SIMPLE_TYPES:
        return WidgetMeta(_SIMPLE_TYPES[_type], {})
    for key in _SIMPLE_TYPES.keys():
        if _is_subclass(tw.outer_type_, key):
            return WidgetMeta(_SIMPLE_TYPES[key], {})

    # TODO:
    # if issubclass(field.type_, Decimal):
    #       precision=getattr(field.type_, "max_digits", None),
    #       scale=getattr(field.type_, "decimal_places", None),
    #     return widgets.FloatSpinBox, {}

    if _type in (types.FunctionType,):
        return widgets.FunctionGui, {"function": tw.default}  # type: ignore

    # sequence of paths
    if tw.shape in SEQUENCE_LIKE:
        if _is_subclass(tw.type_, pathlib.Path):
            return WidgetMeta(widgets.FileEdit, {"mode": "rm"})
        elif tw.shape == SHAPE_LIST:
            return WidgetMeta(widgets.ListEdit, {})
        elif tw.shape == SHAPE_TUPLE:
            return WidgetMeta(widgets.TupleEdit, {})
    return None


_SIMPLE_RETURN_TYPES = [
    bool,
    int,
    float,
    str,
    pathlib.Path,
    datetime.time,
    datetime.date,
    datetime.datetime,
    range,
    slice,
]


def match_return_type(tw: FieldType) -> WidgetMeta | None:
    """Check simple type mappings for result widgets."""
    import sys

    if tw.outer_type_ in _SIMPLE_TYPES:
        return WidgetMeta(widgets.LineEdit, {"gui_only": True})

    if tw.outer_type_ is widgets.Table:
        return WidgetMeta(widgets.Table, {})

    table_types = [
        resolve_annotation(x, sys.modules)
        for x in ("pandas.DataFrame", "numpy.ndarray")
    ]

    if any(
        _is_subclass(tw.outer_type_, tt)
        for tt in table_types
        if not isinstance(tt, ForwardRef)
    ):
        return WidgetMeta(widgets.Table, {})

    return None


def _parse_field(field: ModelField | Field) -> tuple[Any, bool, str]:
    if isinstance(field, Field):
        required = field.default is MISSING and field.default_factory is MISSING
        return field.type, required, field.name
    if isinstance(field, ModelField):
        required = (field.required is Undefined) or field.required
        return field.outer_type_, required, field.name


def _dataclass_field_to_model_field(field: Field) -> ModelField:
    return ModelField(
        name=field.name,
        type_=field.type,
        class_validators={},
        model_config=BaseConfig,
        default=field.default if field.default is not MISSING else None,
        default_factory=None
        if field.default_factory is MISSING
        else field.default_factory,
        required=field.default is MISSING and field.default_factory is MISSING,
    )


def pick_widget_type(
    value: Any = None,
    annotation: type[Any] | FieldType | None = None,
    options: WidgetOptions | None = None,
    is_result: bool = False,
) -> WidgetMeta:
    """Pick the appropriate widget type for ``value`` with ``annotation``."""
    if is_result and annotation is inspect.Parameter.empty:
        annotation = str
    if isinstance(annotation, ModelField):
        tw = annotation
    elif isinstance(annotation, Field):
        tw = _dataclass_field_to_model_field(annotation)
    else:
        try:
            try:
                tw = _temp_field(value, annotation)
            except TypeError:
                tw = _temp_field_no_cache(value, annotation)
        except ConfigError:
            if value is None:
                return WidgetMeta(widgets.EmptyWidget, {"visible": False})
            raise
    options = options or {}

    _type = tw.outer_type_
    options.setdefault("nullable", not tw.required)
    choices = options.get("choices") or (isinstance(_type, EnumMeta) and _type)

    if "widget_type" in options:
        widget_type = options.pop("widget_type")
        if choices:
            if widget_type == "RadioButton":
                widget_type = "RadioButtons"
                warnings.warn(
                    f"widget_type of 'RadioButton' (with dtype {tw._type_display()}) is"
                    " being coerced to 'RadioButtons' due to choices or Enum type.",
                    stacklevel=2,
                )
            options.setdefault("choices", choices)
        return widget_type, options

    # look for subclasses
    for registered_type in _TYPE_DEFS:
        if _type == registered_type or _is_subclass(_type, registered_type):
            _cls, opts = _TYPE_DEFS[registered_type]
            return _cls, {**options, **opts}  # type: ignore

    if is_result:
        _widget_type = match_return_type(tw)
        if _widget_type:
            _cls, opts = _widget_type
            return _cls, {**options, **opts}  # type: ignore
        # Chosen for backwards/test compatibility
        return widgets.LineEdit, {"gui_only": True}

    if choices:
        options["choices"] = choices
        wdg = widgets.Select if options.get("allow_multiple") else widgets.ComboBox
        return wdg, options

    _widget_type = match_type(tw)
    if _widget_type:
        _cls, opts = _widget_type
        return _cls, {**options, **opts}  # type: ignore

    return widgets.EmptyWidget, {"visible": False}


def get_widget_class(
    value: Any = None,
    annotation: type[Any] | FieldType | None = None,
    options: Mapping[str, Any] | None = None,
    is_result: bool = False,
) -> tuple[WidgetClass, WidgetOptions]:
    """Return a WidgetClass appropriate for the given parameters.

    Parameters
    ----------
    value : Any, optional
        A python value.  Will be used to determine the widget type if an ``annotation``
        is not explicitly provided by default None
    annotation : Optional[Type], optional
        A type annotation, by default None
    options : WidgetOptions, optional
        Options to pass when constructing the widget, by default {}
    is_result : bool, optional
        Identifies whether the returned widget should be tailored to
        an input or to an output.

    Returns
    -------
    Tuple[WidgetClass, WidgetOptions]
        The WidgetClass, and WidgetOptions that can be used for params. WidgetOptions
        may be different than the options passed in.
    """
    _options = cast(WidgetOptions, dict(options or {}))

    widget_type, _options = pick_widget_type(value, annotation, _options, is_result)

    if isinstance(widget_type, str):
        widget_class: WidgetClass = _import_class(widget_type)
    else:
        widget_class = widget_type

    if not _is_subclass(widget_class, widgets._bases.Widget):
        assert_protocol(widget_class, WidgetProtocol)

    return widget_class, _options


def _import_class(class_name: str) -> WidgetClass:
    import importlib

    # import from magicgui widgets if not explicitly namespaced
    if "." not in class_name:
        class_name = "magicgui.widgets." + class_name

    mod_name, name = class_name.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, name)


def _validate_return_callback(func):
    try:
        sig = inspect.signature(func)
        # the signature must accept three arguments
        sig.bind(1, 2, 3)  # (gui, result, return_type)
    except TypeError as e:
        raise TypeError(f"object {func!r} is not a valid return callback: {e}")


_T = TypeVar("_T", bound=Type)


@overload
def register_type(
    type_: _T,
    *,
    widget_type: WidgetRef | None = None,
    return_callback: ReturnCallback | None = None,
    **options,
) -> _T:
    ...


@overload
def register_type(
    type_: Literal[None] = None,
    *,
    widget_type: WidgetRef | None = None,
    return_callback: ReturnCallback | None = None,
    **options,
) -> Callable[[_T], _T]:
    ...


def register_type(
    type_: _T | None = None,
    *,
    widget_type: WidgetRef | None = None,
    return_callback: ReturnCallback | None = None,
    **options,
) -> _T | Callable[[_T], _T]:
    """Register a ``widget_type`` to be used for all parameters with type ``type_``.

    Parameters
    ----------
    type_ : type
        The type for which a widget class or return callback will be provided.
    widget_type : WidgetRef, optional
        A widget class from the current backend that should be used whenever ``type_``
        is used as the type annotation for an argument in a decorated function,
        by default None
    return_callback: callable, optional
        If provided, whenever ``type_`` is declared as the return type of a decorated
        function, ``return_callback(widget, value, return_type)`` will be called
        whenever the decorated function is called... where ``widget`` is the Widget
        instance, and ``value`` is the return value of the decorated function.
    **options
        key value pairs where the keys are valid `WidgetOptions`

    Raises
    ------
    ValueError
        If none of `widget_type`, `return_callback`, `bind` or `choices` are provided.
    """
    if all(
        x is None
        for x in [
            return_callback,
            options.get("bind"),
            options.get("choices"),
            widget_type,
        ]
    ):
        raise ValueError(
            "At least one of `widget_type`, `return_callback`, `bind` or `choices` "
            "must be provided."
        )

    def _deco(type_):
        _type_ = _temp_field(None, type_).outer_type_

        if return_callback is not None:
            _validate_return_callback(return_callback)
            _RETURN_CALLBACKS[_type_].append(return_callback)

        _options = cast(WidgetOptions, options)

        if "choices" in _options:
            _TYPE_DEFS[_type_] = (widgets.ComboBox, _options)
            if widget_type is not None:
                warnings.warn(
                    "Providing `choices` overrides `widget_type`. Categorical widget "
                    f"will be used for type {_type_}",
                    stacklevel=2,
                )
        elif widget_type is not None:

            if not isinstance(widget_type, (str, WidgetProtocol)) and not (
                inspect.isclass(widget_type) and issubclass(widget_type, widgets.Widget)
            ):
                raise TypeError(
                    '"widget_type" must be either a string, WidgetProtocol, or '
                    "Widget subclass"
                )
            _TYPE_DEFS[_type_] = (widget_type, _options)
        elif "bind" in _options:
            # if we're binding a value to this parameter, it doesn't matter what type
            # of ValueWidget is used... it usually won't be shown
            _TYPE_DEFS[_type_] = (widgets.EmptyWidget, _options)
        return _type_

    return _deco if type_ is None else _deco(type_)


def _type2callback(type_: type) -> list[ReturnCallback]:
    """Check if return callbacks have been registered for ``type_`` and return if so.

    Parameters
    ----------
    type_ : type
        The type_ to look up.

    Returns
    -------
    list of callable
        Where a return callback accepts two arguments (gui, value) and does something.
    """
    if type_ is inspect.Parameter.empty:
        return []

    # look for direct hits
    tw = _temp_field(None, type_)
    if tw.outer_type_ in _RETURN_CALLBACKS:
        return _RETURN_CALLBACKS[tw.outer_type_]

    # look for subclasses
    for registered_type in _RETURN_CALLBACKS:
        if tw.is_subclass(registered_type):
            return _RETURN_CALLBACKS[registered_type]
    return []


class Config(BaseConfig):
    arbitrary_types_allowed = True


@lru_cache
def _temp_field(value: Any, annotation: Any) -> ModelField:
    if annotation is inspect.Parameter.empty:
        annotation = Undefined
    return ModelField.infer(
        name="_temp",
        value=value,
        annotation=annotation,
        class_validators=None,
        config=Config,
    )


def _temp_field_no_cache(value: Any, annotation: Any) -> ModelField:
    if annotation is inspect.Parameter.empty:
        annotation = Undefined
    return ModelField.infer(
        name="_temp",
        value=value,
        annotation=annotation,
        class_validators=None,
        config=Config,
    )


def resolve_forward_refs(annotation: Any) -> Any:
    """Resolve forward refs in value, using TypeWrapper"""
    if annotation in (None, inspect.Parameter.empty):
        return annotation
    return _temp_field(None, annotation).outer_type_


import sys
from typing import _eval_type  # type: ignore  # noqa


def resolve_annotation(
    annotation: str | type[Any] | None | ForwardRef,
    namespace: Mapping[str, Any] | None = None,
    *,
    allow_import=False,
    raise_=False,
) -> type[Any] | ForwardRef:
    """[summary]

    part of typing.get_type_hints.

    Parameters
    ----------
    annotation : Type[Any]
        Type hint, string, or `None` to resolve
    namespace : Optional[Mapping[str, Any]], optional
        Optional namespace in which to resolve, by default None

    Raises
    ------
    NameError
        If the annotation cannot be resolved with the provided namespace
    """
    if annotation is None:
        annotation = type(None)

    if isinstance(annotation, str):
        kwargs = dict(is_argument=False)
        if (3, 10) > sys.version_info >= (3, 9, 8) or sys.version_info >= (3, 10, 1):
            kwargs["is_class"] = True
        annotation = ForwardRef(annotation, **kwargs)

    try:
        return _eval_type(annotation, namespace, None)
    except NameError as e:
        if allow_import:
            # try to import the top level name and try again
            msg = str(e)
            if msg.startswith("name ") and msg.endswith(" is not defined"):
                from importlib import import_module

                name = msg.split()[1].strip("\"'")
                ns = dict(namespace) if namespace else {}
                if name not in ns:
                    ns[name] = import_module(name)
                    return resolve_annotation(
                        annotation, ns, allow_import=allow_import, raise_=raise_
                    )
        if raise_:
            raise
    return annotation


# ----------------------------------
# V2
# ----------------------------------


from typing import Any, Mapping

from ._notes import WidgetMeta


class _Undefined:
    """
    Sentinel class to indicate the lack of a value when ``None`` is ambiguous.

    ``_Undefined`` is a singleton. There is only ever one of it.

    """

    _singleton = None

    def __new__(cls):
        if _Undefined._singleton is None:
            _Undefined._singleton = super().__new__(cls)
        return _Undefined._singleton

    def __repr__(self):
        return "<Undefined>"

    def __bool__(self):
        return False


Undefined = _Undefined()

# Attribute(
#   name='x', default=NOTHING, validator=None, repr=True, eq=True, eq_key=None,
#   order=True, order_key=None, hash=None, init=True, metadata=mappingproxy({}),
#   type='int', converter=None, kw_only=False, inherited=False, on_setattr=None
# )

from .type_map import pick_widget_type


def prepare_widget(
    type: Any = Undefined,
    default: Any = Undefined,
    *,
    ui_options: Mapping[str, Any] | None = None,
    name: str = "",
    is_output: bool = False,
) -> WidgetMeta:
    ...
    widget_type, _options = pick_widget_type(value, annotation, _options, is_result)
