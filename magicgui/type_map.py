"""Functions in this module are responsible for mapping type annotations to widgets."""
from __future__ import annotations

import datetime
import inspect
import pathlib
import types
import warnings
from collections import defaultdict
from contextlib import contextmanager
from enum import EnumMeta
from typing import (
    Any,
    Callable,
    DefaultDict,
    ForwardRef,
    Iterator,
    Optional,
    Type,
    TypeVar,
    cast,
    overload,
)

from typing_extensions import Literal, get_origin

from magicgui import widgets
from magicgui.types import (
    PathLike,
    ReturnCallback,
    WidgetClass,
    WidgetOptions,
    WidgetRef,
    WidgetTuple,
)
from magicgui.widgets._protocols import WidgetProtocol, assert_protocol

from ._type_wrapper import TypeWrapper, resolve_annotation

__all__: list[str] = ["register_type", "get_widget_class"]


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""


_RETURN_CALLBACKS: DefaultDict[type, list[ReturnCallback]] = defaultdict(list)
_TYPE_DEFS: dict[type, WidgetTuple] = dict()


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
    pathlib.Path: widgets.FileEdit,
    datetime.time: widgets.TimeEdit,
    datetime.date: widgets.DateEdit,
    datetime.datetime: widgets.DateTimeEdit,
    range: widgets.RangeEdit,
    slice: widgets.SliceEdit,
    list: widgets.ListEdit,
    tuple: widgets.TupleEdit,
}


def match_type(tw: TypeWrapper) -> WidgetTuple | None:
    """Check simple type mappings."""
    _type = tw.outer_type_

    if _type in _SIMPLE_ANNOTATIONS:
        return _SIMPLE_ANNOTATIONS[_type], {}

    if _type is widgets.ProgressBar:
        return widgets.ProgressBar, {"bind": lambda widget: widget, "visible": True}

    if _type in _SIMPLE_TYPES:
        return _SIMPLE_TYPES[_type], {}
    for key in _SIMPLE_TYPES.keys():
        if tw.is_subclass(key):
            return _SIMPLE_TYPES[key], {}

    if _type in (types.FunctionType,):
        return widgets.FunctionGui, {"function": tw.default}  # type: ignore

    if tw.shape in tw.SHAPE.SEQUENCE_LIKE:
        if _is_subclass(tw.type_, pathlib.Path):
            # sequence of paths
            return widgets.FileEdit, {"mode": "rm"}
        elif tw.shape == tw.SHAPE.LIST:
            return widgets.ListEdit, {}
        elif tw.shape == tw.SHAPE.TUPLE:
            return widgets.TupleEdit, {}

    if tw.shape == tw.SHAPE.SET:
        if len(_type.__args__) > 0:
            arg = _type.__args__[0]
            if get_origin(arg) is Literal:
                return widgets.Select, {"choices": arg.__args__}

    if get_origin(_type) is Literal:
        return widgets.ComboBox, {"choices": _type.__args__}
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


def match_return_type(tw: TypeWrapper) -> WidgetTuple | None:
    """Check simple type mappings for result widgets."""
    import sys

    if tw.outer_type_ in _SIMPLE_TYPES:
        return widgets.LineEdit, {"gui_only": True}

    if tw.outer_type_ is widgets.Table:
        return widgets.Table, {}

    table_types = [
        resolve_annotation(x, sys.modules)
        for x in ("pandas.DataFrame", "numpy.ndarray")
    ]

    if any(tw.is_subclass(tt) for tt in table_types if not isinstance(tt, ForwardRef)):
        return widgets.Table, {}

    return None


def pick_widget_type(
    value: Any = None,
    annotation: type[Any] | None = None,
    options: WidgetOptions | None = None,
    is_result: bool = False,
    raise_on_unknown: bool = True,
) -> WidgetTuple:
    """Pick the appropriate widget type for ``value`` with ``annotation``."""
    if is_result and annotation is inspect.Parameter.empty:
        annotation = str
    try:
        tw = TypeWrapper(annotation, value)
    except ValueError:
        if value is None:
            return widgets.EmptyWidget, {"visible": False}
        raise
    tw.resolve()
    _type = tw.outer_type_
    options = options or {}
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
        if _type == registered_type or tw.is_subclass(registered_type):
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

    if raise_on_unknown:
        raise ValueError(
            f"No widget found for type {_type} and annotation {annotation}"
        )

    return widgets.EmptyWidget, {"visible": False}


def get_widget_class(
    value: Any = None,
    annotation: type[Any] | None = None,
    options: WidgetOptions | None = None,
    is_result: bool = False,
    raise_on_unknown: bool = True,
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
    raise_on_unknown : bool, optional
        Raise exception if no widget is found for the given type, by default True

    Returns
    -------
    Tuple[WidgetClass, WidgetOptions]
        The WidgetClass, and WidgetOptions that can be used for params. WidgetOptions
        may be different than the options passed in.
    """
    _options = cast(WidgetOptions, options)

    widget_type, _options = pick_widget_type(
        value, annotation, _options, is_result, raise_on_unknown
    )

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
        tw = TypeWrapper(type_)
        tw.resolve()
        _type_ = tw.outer_type_

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


@contextmanager
def type_registered(
    type_: _T,
    *,
    widget_type: WidgetRef | None = None,
    return_callback: ReturnCallback | None = None,
    **options,
) -> Iterator[None]:
    """Context manager that temporarily registers a widget type for a given `type_`.

    When the context is exited, the previous widget type associations for `type_` is
    restored.

    Parameters
    ----------
    type_ : _T
        The type for which a widget class or return callback will be provided.
    widget_type : Optional[WidgetRef]
        A widget class from the current backend that should be used whenever ``type_``
        is used as the type annotation for an argument in a decorated function,
        by default None
    return_callback: Optional[callable]
        If provided, whenever ``type_`` is declared as the return type of a decorated
        function, ``return_callback(widget, value, return_type)`` will be called
        whenever the decorated function is called... where ``widget`` is the Widget
        instance, and ``value`` is the return value of the decorated function.
    **options
        key value pairs where the keys are valid `WidgetOptions`
    """
    tw = TypeWrapper(type_)
    tw.resolve()
    _type_ = tw.outer_type_

    # check if return_callback is already registered
    rc_was_present = return_callback in _RETURN_CALLBACKS.get(_type_, [])
    # store any previous widget_type and options for this type
    prev_type_def: Optional[WidgetTuple] = _TYPE_DEFS.get(_type_, None)
    _type_ = register_type(
        type_, widget_type=widget_type, return_callback=return_callback, **options
    )
    new_type_def: Optional[WidgetTuple] = _TYPE_DEFS.get(_type_, None)
    try:
        yield
    finally:
        # restore things to before the context
        if return_callback is not None and not rc_was_present:
            _RETURN_CALLBACKS[_type_].remove(return_callback)

        if _TYPE_DEFS.get(_type_, None) is not new_type_def:
            warnings.warn("Type definition changed during context", stacklevel=2)

        if prev_type_def is not None:
            _TYPE_DEFS[_type_] = prev_type_def
        else:
            _TYPE_DEFS.pop(_type_, None)


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
    tw = TypeWrapper(type_)
    tw.resolve()
    if tw.outer_type_ in _RETURN_CALLBACKS:
        return _RETURN_CALLBACKS[tw.outer_type_]

    # look for subclasses
    for registered_type in _RETURN_CALLBACKS:
        if tw.is_subclass(registered_type):
            return _RETURN_CALLBACKS[registered_type]
    return []
