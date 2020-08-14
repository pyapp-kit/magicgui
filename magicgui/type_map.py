"""magicgui Widget class that wraps all backend widgets."""
import datetime
import inspect
import pathlib
from collections import abc
from enum import EnumMeta
from typing import Any, Callable, Optional, Set, Type, get_args, get_origin

from magicgui.application import AppRef, use_app
from magicgui.bases import BaseWidget
from magicgui.constants import WidgetKind
from magicgui.subwidgets import MAP


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""

    pass


TypeMatcher = Callable[[Any, Optional[Type], Optional[dict]], Optional[WidgetKind]]
_TYPE_MATCHERS: Set[TypeMatcher] = set()


def type_matcher(func: TypeMatcher) -> TypeMatcher:
    """Add function to the set of type matchers."""
    _TYPE_MATCHERS.add(func)
    return func


@type_matcher
def sequence_of_paths(value, annotation, options) -> Optional[WidgetKind]:
    """Determine if value/annotation is a Sequence[pathlib.Path]."""

    def is_path(v):
        return None

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
def simple_type(value, annotation, options) -> Optional[WidgetKind]:
    """Check simple type mappings."""
    dtype = (get_origin(annotation) or annotation) if annotation else type(value)

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


def pick_widget_type(
    value: Any = None, annotation: Optional[Type] = None, options: dict = {},
) -> Optional[WidgetKind]:
    """Pick the appropriate magicgui widget type for ``value`` with ``annotation``."""
    if "widget_type" in options:
        return WidgetKind(options["widget_type"])

    dtype = (get_origin(annotation) or annotation) if annotation else type(value)

    if isinstance(dtype, EnumMeta) or "choices" in options:
        return WidgetKind.COMBO_BOX

    for matcher in _TYPE_MATCHERS:
        widget_type = matcher(value, annotation, options)
        if widget_type:
            return widget_type
    return None


def _get_backend_widget(widget_type: WidgetKind, app: AppRef) -> Type[BaseWidget]:
    _app = use_app(app)
    try:
        return _app.get_obj(widget_type.value)
    except AttributeError:
        # TODO: Cleanup?
        val = widget_type.value
        for key, func in MAP.items():
            if val.startswith(key):
                subval = val[len(key) :]  # noqa
                try:
                    superclass: Type[BaseWidget] = _app.get_obj(subval)
                    return func(superclass)
                except AttributeError:
                    pass
    raise MissingWidget(
        f"Could not find an implementation of widget type {widget_type.value!r} "
        f"in backend {_app.backend_name!r}\n"
        f"Looked in: {_app.backend_module!r}"
    )
