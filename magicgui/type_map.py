"""Functions in this module are responsible for mapping type annotations to widgets."""
from __future__ import annotations

import datetime
import inspect
import pathlib
import sys
import types
import warnings
from collections import abc, defaultdict
from enum import EnumMeta
from typing import Any, DefaultDict, ForwardRef, Union, cast

from typing_extensions import get_args, get_origin

from magicgui import widgets
from magicgui.types import (
    PathLike,
    ReturnCallback,
    TypeMatcher,
    WidgetClass,
    WidgetOptions,
    WidgetRef,
    WidgetTuple,
)
from magicgui.widgets._protocols import WidgetProtocol, assert_protocol

__all__: list[str] = ["register_type", "get_widget_class", "type_matcher"]


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""


_RETURN_CALLBACKS: DefaultDict[type, list[ReturnCallback]] = defaultdict(list)
_TYPE_MATCHERS: list[TypeMatcher] = list()
_TYPE_DEFS: dict[type, WidgetTuple] = dict()


def _is_subclass(obj, superclass):
    """Safely check if obj is a subclass of superclass."""
    try:
        return issubclass(obj, superclass)
    except Exception:
        return False


def _evaluate_forwardref(type_: Any) -> Any:
    """Convert typing.ForwardRef into an actual object."""
    if isinstance(type_, str):
        type_ = ForwardRef(type_)

    if not isinstance(type_, ForwardRef):
        return type_

    from importlib import import_module

    try:
        _module = type_.__forward_arg__.split(".", maxsplit=1)[0]
        globalns = globals().copy()
        globalns.update({_module: import_module(_module)})
    except ImportError as e:
        raise ImportError(
            "Could not resolve the magicgui forward reference annotation: "
            f"{type_.__forward_arg__!r}."
        ) from e

    if sys.version_info < (3, 9):
        return type_._evaluate(globalns, {})
    # Even though it is the right signature for python 3.9, mypy complains with
    # `error: Too many arguments for "_evaluate" of "ForwardRef"` hence the cast...
    return cast(Any, type_)._evaluate(globalns, {}, set())


def _normalize_type(value: Any, annotation: Any) -> tuple[type, bool]:
    """Return annotation type origin or dtype of value."""
    if not annotation:
        return type(value), False
    if annotation is inspect.Parameter.empty:
        return type(value), False

    # look for Optional[Type], which manifests as Union[Type, None]
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Union and len(args) == 2 and type(None) in args:
        type_ = next(i for i in args if not issubclass(i, type(None)))
        return type_, True
    return (origin or annotation), False


def type_matcher(func: TypeMatcher) -> TypeMatcher:
    """Add function to the set of type matchers.

    Example
    -------
    >>> @type_matcher
    ... def str_to_line_edit(value, annotation):
    ...     if annotation in (str, 'str') or type(str) is str:
    ...         return widgets.LineEdit, {}
    """
    _TYPE_MATCHERS.append(func)
    return func


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
}


@type_matcher
def simple_types(value, annotation) -> WidgetTuple | None:
    """Check simple type mappings."""
    if annotation in _SIMPLE_ANNOTATIONS:
        return _SIMPLE_ANNOTATIONS[annotation], {}

    dtype, optional = _normalize_type(value, annotation)

    if dtype is widgets.ProgressBar:
        return widgets.ProgressBar, {"bind": lambda widget: widget, "visible": True}

    if dtype in _SIMPLE_TYPES:
        return _SIMPLE_TYPES[dtype], {}
    else:
        for key in _SIMPLE_TYPES.keys():
            if _is_subclass(dtype, key):
                return _SIMPLE_TYPES[key], {}
    return None


@type_matcher
def callable_type(value, annotation) -> WidgetTuple | None:
    """Determine if value/annotation is a function type."""
    dtype, optional = _normalize_type(value, annotation)

    if dtype in (types.FunctionType,):
        return widgets.FunctionGui, {"function": value}  # type: ignore
    return None


@type_matcher
def sequence_of_paths(value, annotation) -> WidgetTuple | None:
    """Determine if value/annotation is a Sequence[pathlib.Path]."""
    if annotation:
        orig = get_origin(annotation)
        args = get_args(annotation)
        if not (inspect.isclass(orig) and args):
            return None
        if _is_subclass(orig, abc.Sequence) or isinstance(orig, abc.Sequence):
            if _is_subclass(args[0], pathlib.Path):
                return widgets.FileEdit, {"mode": "rm"}
    elif value:
        if isinstance(value, abc.Sequence) and all(
            isinstance(v, pathlib.Path) for v in value
        ):
            return widgets.FileEdit, {"mode": "rm"}
    return None


def pick_widget_type(
    value: Any = None, annotation: type | None = None, options: WidgetOptions = {}
) -> WidgetTuple:
    """Pick the appropriate widget type for ``value`` with ``annotation``."""
    annotation = _evaluate_forwardref(annotation)
    dtype, optional = _normalize_type(value, annotation)
    if optional:
        options.setdefault("nullable", True)
    choices = options.get("choices") or (isinstance(dtype, EnumMeta) and dtype)

    if "widget_type" in options:
        widget_type = options.pop("widget_type")
        if choices:
            if widget_type == "RadioButton":
                widget_type = "RadioButtons"
                warnings.warn(
                    f"widget_type of 'RadioButton' (with dtype {dtype}) is being "
                    "coerced to 'RadioButtons' due to choices or Enum type."
                )
            options.setdefault("choices", choices)
        return widget_type, options

    # look for subclasses
    for registered_type in _TYPE_DEFS:
        if dtype == registered_type or _is_subclass(dtype, registered_type):
            return _TYPE_DEFS[registered_type]

    if choices:
        return widgets.ComboBox, {"choices": choices}

    for matcher in _TYPE_MATCHERS:
        _widget_type = matcher(value, annotation)
        if _widget_type:
            return _widget_type

    return widgets.EmptyWidget, {"visible": False}


def get_widget_class(
    value: Any = None, annotation: type | None = None, options: WidgetOptions = {}
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

    Returns
    -------
    Tuple[WidgetClass, WidgetOptions]
        The WidgetClass, and WidgetOptions that can be used for params. WidgetOptions
        may be different than the options passed in.
    """
    _options = cast(WidgetOptions, options)
    widget_type, _options = pick_widget_type(value, annotation, _options)

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


def register_type(
    type_: type,
    *,
    widget_type: WidgetRef = None,
    return_callback: ReturnCallback | None = None,
    **options,
):
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
        If both ``widget_type`` and ``choices`` are None
    """
    type_ = _evaluate_forwardref(type_)

    if not (
        return_callback or options.get("bind") or options.get("choices") or widget_type
    ):
        raise ValueError(
            "At least one of `widget_type`, `return_callback`, `bind` or `choices` "
            "must be provided."
        )

    if return_callback is not None:
        _validate_return_callback(return_callback)
        _RETURN_CALLBACKS[type_].append(return_callback)

    _options = cast(WidgetOptions, options)

    if "choices" in _options:
        _choices = _options["choices"]

        if not isinstance(_choices, EnumMeta) and callable(_choices):
            _options["choices"] = _check_choices(_choices)
        _TYPE_DEFS[type_] = (widgets.ComboBox, _options)
        if widget_type is not None:
            warnings.warn(
                "Providing `choices` overrides `widget_type`. Categorical widget will "
                f"be used for type {type_}"
            )
    elif widget_type is not None:

        if not isinstance(widget_type, (str, widgets._bases.Widget, WidgetProtocol)):
            raise TypeError(
                '"widget_type" must be either a string, Widget, or WidgetProtocol'
            )
        _TYPE_DEFS[type_] = (widget_type, _options)
    elif "bind" in _options:
        # if we're binding a value to this parameter, it doesn't matter what type
        # of ValueWidget is used... it usually won't be shown
        _TYPE_DEFS[type_] = (widgets.EmptyWidget, _options)
    return None


def _check_choices(choices):
    """Catch pre 0.2.0 API from developers using register_type."""
    n_params = len(inspect.signature(choices).parameters)
    if n_params > 1:
        warnings.warn(
            "\n\nDEVELOPER NOTICE: As of magicgui 0.2.0, when providing a callable to "
            "`choices`, the\ncallable may accept only a single positional "
            "argument (which will be an instance of\n"
            "`magicgui.widgets._bases.CategoricalWidget`), and must "
            "return an iterable (the choices\nto show).  Function "
            f"'{choices.__module__}.{choices.__name__}' accepts {n_params} "
            "arguments.\nIn the future, this will raise an exception.\n",
            DeprecationWarning,
        )

        def wrapper(obj):
            return choices(obj.native, obj.annotation)

        return wrapper
    return choices


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
    # look for direct hits
    type_ = _evaluate_forwardref(type_)
    if type_ in _RETURN_CALLBACKS:
        return _RETURN_CALLBACKS[type_]
    # look for subclasses
    for registered_type in _RETURN_CALLBACKS:
        if _is_subclass(type_, registered_type):
            return _RETURN_CALLBACKS[registered_type]
    return []
