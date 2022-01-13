"""Functions in this module are responsible for mapping type annotations to widgets."""
from __future__ import annotations

import datetime
import inspect
import pathlib
import sys
import warnings
from collections import defaultdict
from enum import EnumMeta
from typing import (
    Any,
    Callable,
    DefaultDict,
    ForwardRef,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from typing_extensions import Literal, get_args, get_origin

from magicgui import widgets
from magicgui.types import (
    ReturnCallback,
    ReturnMatcher,
    WidgetClass,
    WidgetOptions,
    WidgetRef,
    WidgetTuple,
)
from magicgui.widgets._protocols import WidgetProtocol, assert_protocol

__all__: list[str] = ["register_type", "get_widget_class", "return_matcher"]


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""


_RETURN_CALLBACKS: DefaultDict[type, list[ReturnCallback]] = defaultdict(list)
_RETURN_MATCHERS: list[ReturnMatcher] = list()
_TYPE_DEFS: dict[type, WidgetTuple] = dict()


def _is_subclass(obj, superclass):
    """Safely check if obj is a subclass of superclass."""
    try:
        return issubclass(obj, superclass)
    except Exception:
        return False


# TODO: copied from type_map
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
        type_ = next(i for i in args if not isinstance(i, type(None)))
        return type_, True
    return (origin or annotation), False


def return_matcher(func: ReturnMatcher) -> ReturnMatcher:
    """Add function to the set of return matchers.

    Example
    -------
    >>> @return
    ... def default_return_widget(value, annotation):
    ...     return widgets.LineEdit, {}
    """
    _RETURN_MATCHERS.append(func)
    return func


_SIMPLE_TYPES = [
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


@return_matcher
def default_return_matcher(value, annotation) -> WidgetTuple | None:
    """Checks for 'simple' types that fit in a LineEdit."""
    dtype, optional = _normalize_type(value, annotation)
    if dtype in _SIMPLE_TYPES:
        return widgets.LineEdit, {"gui_only": True}
    else:
        return None


@return_matcher
def tabular_return_matcher(value, annotation) -> WidgetTuple | None:
    """Checks for tabular data."""
    # TODO: is this correct?
    if annotation == inspect._empty:
        return None
    dtype, optional = _normalize_type(value, annotation)
    args = [_evaluate_forwardref(a) for a in get_args(widgets._table.TableData)]
    if dtype in args:
        return widgets.Table, {}

    return None


def pick_widget_type(
    value: Any = None,
    annotation: type | None = None,
    options: WidgetOptions | None = None,
) -> WidgetTuple:
    """Pick the appropriate widget type for ``value`` with ``annotation``."""
    options = options or {}
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
                    "coerced to 'RadioButtons' due to choices or Enum type.",
                    stacklevel=2,
                )
            options.setdefault("choices", choices)
        return widget_type, options

    # look for subclasses
    for registered_type in _TYPE_DEFS:
        if dtype == registered_type or _is_subclass(dtype, registered_type):
            _cls, opts = _TYPE_DEFS[registered_type]
            return _cls, {**options, **opts}  # type: ignore

    for matcher in _RETURN_MATCHERS:
        _widget_type = matcher(value, annotation)
        if _widget_type:
            _cls, opts = _widget_type
            return _cls, {**options, **opts}  # type: ignore

    return widgets.LineEdit, {
        "gui_only": True
    }  # Chosen for backwards/test compatibility


def get_widget_class(
    value: Any = None,
    annotation: type | None = None,
    options: WidgetOptions | None = None,
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
        _type_ = _evaluate_forwardref(type_)

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

            if not isinstance(
                widget_type, (str, widgets._bases.Widget, WidgetProtocol)
            ):
                raise TypeError(
                    '"widget_type" must be either a string, Widget, or WidgetProtocol'
                )
            _TYPE_DEFS[_type_] = (widget_type, _options)
        elif "bind" in _options:
            # if we're binding a value to this parameter, it doesn't matter what type
            # of ValueWidget is used... it usually won't be shown
            _TYPE_DEFS[_type_] = (widgets.EmptyWidget, _options)
        return _type_

    return _deco if type_ is None else _deco(type_)
