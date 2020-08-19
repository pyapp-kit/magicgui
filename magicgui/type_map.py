"""magicgui Widget class that wraps all backend widgets."""
import datetime
import inspect
import pathlib
from collections import abc
from enum import EnumMeta
from typing import Any, Callable, Optional, Set, Type, get_args, get_origin

from magicgui.constants import WidgetKind


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""

    pass


TypeMatcher = Callable[[Any, Optional[Type]], Optional[WidgetKind]]
_TYPE_MATCHERS: Set[TypeMatcher] = set()


def type_matcher(func: TypeMatcher) -> TypeMatcher:
    """Add function to the set of type matchers."""
    _TYPE_MATCHERS.add(func)
    return func


@type_matcher
def sequence_of_paths(value, annotation) -> Optional[WidgetKind]:
    """Determine if value/annotation is a Sequence[pathlib.Path]."""

    if annotation:
        orig = get_origin(annotation)
        args = get_args(annotation)
        if not (inspect.isclass(orig) and args):
            return None
        if isinstance(orig, abc.Sequence):
            if inspect.isclass(args[0]) and issubclass(args[0], pathlib.Path):
                return WidgetKind.FILE_EDIT
    elif value:
        if isinstance(value, abc.Sequence) and all(
            isinstance(v, pathlib.Path) for v in value
        ):
            return WidgetKind.FILE_EDIT
    return None


@type_matcher
def simple_type(value, annotation) -> Optional[WidgetKind]:
    """Check simple type mappings."""
    dtype = resolve_type(value, annotation)

    simple = {
        bool: WidgetKind.CHECK_BOX,
        int: WidgetKind.SPIN_BOX,
        float: WidgetKind.FLOAT_SPIN_BOX,
        str: WidgetKind.LINE_EDIT,
        pathlib.Path: WidgetKind.FILE_EDIT,
        datetime.datetime: WidgetKind.DATE_TIME_EDIT,
        type(None): WidgetKind.LINE_EDIT,
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
) -> WidgetKind:
    """Pick the appropriate magicgui widget type for ``value`` with ``annotation``."""
    if "widget_type" in options:
        return WidgetKind(options["widget_type"])

    dtype = resolve_type(value, annotation)

    if isinstance(dtype, EnumMeta) or "choices" in options:
        return WidgetKind.COMBO_BOX

    for matcher in _TYPE_MATCHERS:
        widget_type = matcher(value, annotation)
        if widget_type:
            return widget_type
    raise ValueError("Could not pick widget.")
