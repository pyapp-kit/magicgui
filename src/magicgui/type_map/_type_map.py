"""Functions in this module are responsible for mapping type annotations to widgets."""

from __future__ import annotations

import datetime
import inspect
import itertools
import os
import pathlib
import sys
import types
import warnings
from collections import defaultdict
from contextlib import contextmanager
from enum import EnumMeta
from typing import (
    Any,
    Callable,
    Dict,
    ForwardRef,
    Iterator,
    Literal,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from typing_extensions import Annotated, get_args, get_origin

from magicgui import widgets
from magicgui._type_resolution import resolve_single_type
from magicgui._util import safe_issubclass
from magicgui.types import PathLike, ReturnCallback, Undefined, _Undefined
from magicgui.widgets.protocols import WidgetProtocol, assert_protocol

__all__: list[str] = ["register_type", "get_widget_class"]


# redefining these here for the sake of sphinx autodoc forward refs
WidgetClass = Union[Type[widgets.Widget], Type[WidgetProtocol]]
WidgetRef = Union[str, WidgetClass]
WidgetTuple = Tuple[WidgetRef, Dict[str, Any]]


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""


_RETURN_CALLBACKS: defaultdict[type, list[ReturnCallback]] = defaultdict(list)
_TYPE_DEFS: dict[type, WidgetTuple] = {}


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
    datetime.timedelta: widgets.TimeEdit,
    datetime.date: widgets.DateEdit,
    datetime.datetime: widgets.DateTimeEdit,
    range: widgets.RangeEdit,
    slice: widgets.SliceEdit,
    list: widgets.ListEdit,
    tuple: widgets.TupleEdit,
    os.PathLike: widgets.FileEdit,
}


def match_type(type_: Any, default: Any | None = None) -> WidgetTuple | None:
    """Check simple type mappings."""
    if type_ in _SIMPLE_ANNOTATIONS:
        return _SIMPLE_ANNOTATIONS[type_], {}

    if type_ is widgets.ProgressBar:
        return widgets.ProgressBar, {"bind": lambda widget: widget, "visible": True}

    if type_ in _SIMPLE_TYPES:
        return _SIMPLE_TYPES[type_], {}
    for key in _SIMPLE_TYPES.keys():
        if safe_issubclass(type_, key):
            return _SIMPLE_TYPES[key], {}

    if type_ in (types.FunctionType,):
        return widgets.FunctionGui, {"function": default}

    origin = get_origin(type_) or type_
    choices, nullable = _literal_choices(type_)
    if choices is not None:  # it's a Literal type
        return widgets.ComboBox, {"choices": choices, "nullable": nullable}

    # sequence of paths
    if safe_issubclass(origin, Sequence):
        args = get_args(type_)
        if len(args) == 1 and safe_issubclass(args[0], pathlib.Path):
            return widgets.FileEdit, {"mode": "rm"}
        elif safe_issubclass(origin, list):
            return widgets.ListEdit, {}
        elif safe_issubclass(origin, tuple):
            return widgets.TupleEdit, {}

    if safe_issubclass(origin, Set):
        for arg in get_args(type_):
            if get_origin(arg) is Literal:
                return widgets.Select, {"choices": get_args(arg)}

    pint = sys.modules.get("pint")
    if pint and safe_issubclass(origin, pint.Quantity):
        return widgets.QuantityEdit, {}

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


def match_return_type(type_: Any) -> WidgetTuple | None:
    """Check simple type mappings for result widgets."""
    if type_ in _SIMPLE_TYPES:
        return widgets.LineEdit, {"gui_only": True}

    if type_ is widgets.Table:
        return widgets.Table, {}

    table_types = [
        resolve_single_type(x) for x in ("pandas.DataFrame", "numpy.ndarray")
    ]

    if any(
        safe_issubclass(type_, tt)
        for tt in table_types
        if not isinstance(tt, ForwardRef)
    ):
        return widgets.Table, {}

    return None


def _is_none_type(type_: Any) -> bool:
    return any(type_ is x for x in {None, type(None), Literal[None]})


def _type_optional(
    default: Any = Undefined,
    annotation: type[Any] | _Undefined = Undefined,
) -> tuple[Any, bool]:
    type_ = annotation
    if annotation in (Undefined, None, inspect.Parameter.empty):
        if default is not Undefined:
            type_ = type(default)
    else:
        try:
            type_ = resolve_single_type(annotation)
        except (NameError, ImportError) as e:
            raise type(e)(f"Magicgui could not resolve {annotation}: {e}") from e

    # look for Optional[Type], which manifests as Union[Type, None]
    nullable = default is None
    if type_ is not Undefined:
        args = get_args(type_)
        for arg in args:
            if _is_none_type(arg) or arg is Any or arg is object:
                nullable = True
                if len(args) == 2:
                    type_ = next(i for i in args if i is not arg)
                break

    return type_, nullable


def _literal_choices(annotation: Any) -> tuple[list | None, bool]:
    """Return choices and nullable for a Literal type.

    if annotation is not a Literal type, returns (None, False)
    """
    origin = get_origin(annotation) or annotation
    choices: list | None = None
    nullable = False
    if origin is Literal:
        choices = []
        for choice in get_args(annotation):
            if choice is None:
                nullable = True
            else:
                choices.append(choice)
    return choices, nullable


def _pick_widget_type(
    value: Any = Undefined,
    annotation: Any = Undefined,
    options: dict | None = None,
    is_result: bool = False,
    raise_on_unknown: bool = True,
) -> WidgetTuple:
    """Pick the appropriate widget type for ``value`` with ``annotation``."""
    annotation, options_ = _split_annotated_type(annotation)
    options = {**options_, **(options or {})}
    choices = options.get("choices")

    if is_result and annotation is inspect.Parameter.empty:
        annotation = str

    if (
        value is Undefined
        and annotation in (Undefined, inspect.Parameter.empty)
        and not choices
        and "widget_type" not in options
    ):
        return widgets.EmptyWidget, {"visible": False, **options}

    type_, optional = _type_optional(value, annotation)
    options.setdefault("nullable", optional)
    choices = choices or (isinstance(type_, EnumMeta) and type_)
    literal_choices, nullable = _literal_choices(annotation)
    if literal_choices is not None:
        choices = literal_choices
        options["nullable"] = nullable

    if "widget_type" in options:
        widget_type = options.pop("widget_type")
        if choices:
            if widget_type == "RadioButton":
                widget_type = "RadioButtons"
                warnings.warn(
                    f"widget_type of 'RadioButton' (with dtype {type_}) is"
                    " being coerced to 'RadioButtons' due to choices or Enum type.",
                    stacklevel=2,
                )
            options.setdefault("choices", choices)
        return widget_type, options

    # look for subclasses
    for registered_type in _TYPE_DEFS:
        if type_ == registered_type or safe_issubclass(type_, registered_type):
            cls_, opts = _TYPE_DEFS[registered_type]
            return cls_, {**options, **opts}

    if is_result:
        widget_type_ = match_return_type(type_)
        if widget_type_:
            cls_, opts = widget_type_
            return cls_, {**opts, **options}
        # Chosen for backwards/test compatibility
        return widgets.LineEdit, {"gui_only": True}

    if choices:
        options["choices"] = choices
        wdg = widgets.Select if options.get("allow_multiple") else widgets.ComboBox
        return wdg, options

    widget_type_ = match_type(type_, value)
    if widget_type_:
        cls_, opts = widget_type_
        return cls_, {**opts, **options}

    if raise_on_unknown:
        raise ValueError(
            f"No widget found for type {type_} and annotation {annotation!r}"
        )

    options["visible"] = False
    return widgets.EmptyWidget, options


def _split_annotated_type(annotation: Any) -> tuple[Any, dict]:
    """Split an Annotated type into its base type and options dict."""
    if get_origin(annotation) is not Annotated:
        return annotation, {}

    type_, meta_, *_ = get_args(annotation)

    try:
        meta = dict(meta_)
    except TypeError:
        meta = {}

    return type_, meta


def get_widget_class(
    value: Any = Undefined,
    annotation: Any = Undefined,
    options: dict | None = None,
    is_result: bool = False,
    raise_on_unknown: bool = True,
) -> tuple[WidgetClass, dict]:
    """Return a [Widget][magicgui.widgets.Widget] subclass for the `value`/`annotation`.

    Parameters
    ----------
    value : Any, optional
        A python value.  Will be used to determine the widget type if an ``annotation``
        is not explicitly provided by default None
    annotation : Optional[Type], optional
        A type annotation, by default None
    options : dict, optional
        Options to pass when constructing the widget, by default {}
    is_result : bool, optional
        Identifies whether the returned widget should be tailored to
        an input or to an output.
    raise_on_unknown : bool, optional
        Raise exception if no widget is found for the given type, by default True

    Returns
    -------
    Tuple[WidgetClass, dict]
        The WidgetClass, and dict that can be used for params. dict
        may be different than the options passed in.
    """
    widget_type, options_ = _pick_widget_type(
        value, annotation, options, is_result, raise_on_unknown
    )

    if isinstance(widget_type, str):
        widget_class = _import_wdg_class(widget_type)
    else:
        widget_class = widget_type

    if not safe_issubclass(widget_class, widgets.bases.Widget):
        assert_protocol(widget_class, WidgetProtocol)

    return widget_class, options_


def _import_wdg_class(class_name: str) -> WidgetClass:
    import importlib

    # import from magicgui widgets if not explicitly namespaced
    if "." not in class_name:
        class_name = f"magicgui.widgets.{class_name}"

    mod_name, name = class_name.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return cast(WidgetClass, getattr(mod, name))


def _validate_return_callback(func: Callable) -> None:
    try:
        sig = inspect.signature(func)
        # the signature must accept three arguments
        sig.bind(1, 2, 3)  # (gui, result, return_type)
    except TypeError as e:
        raise TypeError(f"object {func!r} is not a valid return callback: {e}") from e


_T = TypeVar("_T", bound=type)


def _register_type_callback(
    resolved_type: _T,
    return_callback: ReturnCallback | None = None,
) -> list[type]:
    modified_callbacks = []
    if return_callback is None:
        return []
    _validate_return_callback(return_callback)
    # if the type is a Union, add the callback to all of the types in the union
    # (except NoneType)
    if get_origin(resolved_type) is Union:
        for type_per in _generate_union_variants(resolved_type):
            if return_callback not in _RETURN_CALLBACKS[type_per]:
                _RETURN_CALLBACKS[type_per].append(return_callback)
                modified_callbacks.append(type_per)

        for t in get_args(resolved_type):
            if not _is_none_type(t) and return_callback not in _RETURN_CALLBACKS[t]:
                _RETURN_CALLBACKS[t].append(return_callback)
                modified_callbacks.append(t)
    elif return_callback not in _RETURN_CALLBACKS[resolved_type]:
        _RETURN_CALLBACKS[resolved_type].append(return_callback)
        modified_callbacks.append(resolved_type)
    return modified_callbacks


def _register_widget(
    resolved_type: _T,
    widget_type: WidgetRef | None = None,
    **options: Any,
) -> WidgetTuple | None:
    _options = cast(dict, options)

    previous_widget = _TYPE_DEFS.get(resolved_type)

    if "choices" in _options:
        _TYPE_DEFS[resolved_type] = (widgets.ComboBox, _options)
        if widget_type is not None:
            warnings.warn(
                "Providing `choices` overrides `widget_type`. Categorical widget "
                f"will be used for type {resolved_type}",
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
        _TYPE_DEFS[resolved_type] = (widget_type, _options)
    elif "bind" in _options:
        # if we're binding a value to this parameter, it doesn't matter what type
        # of ValueWidget is used... it usually won't be shown
        _TYPE_DEFS[resolved_type] = (widgets.EmptyWidget, _options)
    return previous_widget


@overload
def register_type(
    type_: _T,
    *,
    widget_type: WidgetRef | None = None,
    return_callback: ReturnCallback | None = None,
    **options: Any,
) -> _T: ...


@overload
def register_type(
    type_: Literal[None] | None = None,
    *,
    widget_type: WidgetRef | None = None,
    return_callback: ReturnCallback | None = None,
    **options: Any,
) -> Callable[[_T], _T]: ...


def register_type(
    type_: _T | None = None,
    *,
    widget_type: WidgetRef | None = None,
    return_callback: ReturnCallback | None = None,
    **options: Any,
) -> _T | Callable[[_T], _T]:
    """Register a ``widget_type`` to be used for all parameters with type ``type_``.

    Note: registering a Union (or Optional) type effectively registers all types in
    the union with the arguments.

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
    options
        key value pairs where the keys are valid `dict`

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

    def _deco(type__: _T) -> _T:
        resolved_type = resolve_single_type(type__)
        _register_type_callback(resolved_type, return_callback)
        _register_widget(resolved_type, widget_type, **options)
        return type__

    return _deco if type_ is None else _deco(type_)


@contextmanager
def type_registered(
    type_: _T,
    *,
    widget_type: WidgetRef | None = None,
    return_callback: ReturnCallback | None = None,
    **options: Any,
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
    options
        key value pairs where the keys are valid `dict`
    """
    resolved_type = resolve_single_type(type_)

    # store any previous widget_type and options for this type

    revert_list = _register_type_callback(resolved_type, return_callback)
    prev_type_def = _register_widget(resolved_type, widget_type, **options)

    new_type_def: WidgetTuple | None = _TYPE_DEFS.get(resolved_type, None)
    try:
        yield
    finally:
        # restore things to before the context
        if return_callback is not None:  # this if is only for mypy
            for return_callback_type in revert_list:
                _RETURN_CALLBACKS[return_callback_type].remove(return_callback)

        if _TYPE_DEFS.get(resolved_type, None) is not new_type_def:
            warnings.warn("Type definition changed during context", stacklevel=2)

        if prev_type_def is not None:
            _TYPE_DEFS[resolved_type] = prev_type_def
        else:
            _TYPE_DEFS.pop(resolved_type, None)


def type2callback(type_: type) -> list[ReturnCallback]:
    """Return any callbacks that have been registered for ``type_``.

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

    # look for direct hits ...
    # if it's an Optional, we need to look for the type inside the Optional
    type_ = resolve_single_type(type_)
    if type_ in _RETURN_CALLBACKS:
        return _RETURN_CALLBACKS[type_]

    # look for subclasses
    for registered_type in _RETURN_CALLBACKS:  # sourcery skip: use-next
        if safe_issubclass(type_, registered_type):
            return _RETURN_CALLBACKS[registered_type]
    return []


def _generate_union_variants(type_: Any) -> Iterator[type]:
    type_args = get_args(type_)
    for i in range(2, len(type_args) + 1):
        for per in itertools.combinations(type_args, i):
            yield cast(type, Union[per])
