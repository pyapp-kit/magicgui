"""magicgui Widget class that wraps all backend widgets."""
import datetime
import inspect
import pathlib
from collections import abc
from enum import EnumMeta
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Optional,
    Set,
    Type,
    Union,
    get_args,
    get_origin,
)

from magicgui import widgets
from magicgui.protocols import WidgetProtocol

if TYPE_CHECKING:
    from magicgui.widget_wrappers import Widget


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""

    pass


WidgetClass = Union[Type["Widget"], Type[WidgetProtocol]]
WidgetClassRef = Union[str, WidgetClass]
TypeMatcher = Callable[[Any, Optional[Type]], Optional[WidgetClassRef]]
_TYPE_MATCHERS: Set[TypeMatcher] = set()


def type_matcher(func: TypeMatcher) -> TypeMatcher:
    """Add function to the set of type matchers."""
    _TYPE_MATCHERS.add(func)
    return func


@type_matcher
def sequence_of_paths(value, annotation) -> Optional[WidgetClassRef]:
    """Determine if value/annotation is a Sequence[pathlib.Path]."""

    if annotation:
        orig = get_origin(annotation)
        args = get_args(annotation)
        if not (inspect.isclass(orig) and args):
            return None
        if isinstance(orig, abc.Sequence):
            if inspect.isclass(args[0]) and issubclass(args[0], pathlib.Path):
                return widgets.FileEdit
    elif value:
        if isinstance(value, abc.Sequence) and all(
            isinstance(v, pathlib.Path) for v in value
        ):
            return widgets.FileEdit
    return None


@type_matcher
def simple_type(value, annotation) -> Optional[WidgetClassRef]:
    """Check simple type mappings."""
    dtype = resolve_type(value, annotation)

    simple = {
        bool: widgets.CheckBox,
        int: widgets.SpinBox,
        float: widgets.FloatSpinBox,
        str: widgets.LineEdit,
        pathlib.Path: widgets.FileEdit,
        datetime.datetime: widgets.DateTimeEdit,
        type(None): widgets.LineEdit,
    }
    if dtype in simple:
        return simple[dtype]
    else:
        for key in simple.keys():
            if inspect.isclass(dtype) and issubclass(dtype, key):
                return simple[key]
    return None


def resolve_type(value: Any, annotation: Any) -> Type:
    return (get_origin(annotation) or annotation) if annotation else type(value)


def pick_widget_type(
    value: Any = None, annotation: Optional[Type] = None, options: dict = {},
) -> WidgetClassRef:
    """Pick the appropriate magicgui widget type for ``value`` with ``annotation``."""
    if "widget_type" in options:
        return options["widget_type"]

    dtype = resolve_type(value, annotation)

    if isinstance(dtype, EnumMeta) or "choices" in options:
        return "magicgui.widgets.ComboBox"

    for matcher in _TYPE_MATCHERS:
        widget_type = matcher(value, annotation)
        if widget_type:
            return widget_type
    raise ValueError("Could not pick widget.")


def get_widget_class(
    value: Any = None, annotation: Optional[Type] = None, options: dict = {}
) -> WidgetClass:
    from magicgui.widget_wrappers import Widget

    widget_type = pick_widget_type(value, annotation, options)
    if isinstance(widget_type, str):
        widget_class: WidgetClass = _import_class(widget_type)
    else:
        widget_class = widget_type

    assert isinstance(widget_class, WidgetProtocol) or issubclass(widget_class, Widget)
    return widget_class


def _import_class(class_name: str) -> WidgetClass:
    import importlib

    mod_name, name = class_name.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, name)
