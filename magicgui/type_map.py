"""magicgui Widget class that wraps all backend widgets."""
import datetime
import inspect
import pathlib
from collections import abc
from enum import Enum, EnumMeta, auto
from typing import Any, Callable, Optional, Set, Type, Union, get_args, get_origin

from magicgui.application import AppRef, use_app
from magicgui.base import BaseWidget
from magicgui.utils import camel2snake, snake2camel


class MissingWidget(RuntimeError):
    """Raised when a backend widget cannot be found."""

    pass


class _WidgetKindMeta(EnumMeta):
    def __call__(cls, value, *a, **kw):
        if isinstance(value, str):
            value = snake2camel(value) if "_" in value else value
        return super().__call__(value, *a, **kw)


class WidgetKind(Enum, metaclass=_WidgetKindMeta):
    """Known kinds of widgets.  CamelCase versions used for backend lookup."""

    def _generate_next_value_(name, start, count, last_values):
        return snake2camel(name)

    # Text
    LABEL = auto()
    LINE_EDIT = auto()
    TEXT_EDIT = auto()
    # Numbers
    SPIN_BOX = auto()
    FLOAT_SPIN_BOX = auto()
    SLIDER = auto()
    FLOAT_SLIDER = auto()
    LOG_SLIDER = auto()
    # SCROLL_BAR = auto()
    # Buttons
    PUSH_BUTTON = auto()
    CHECK_BOX = auto()
    RADIO_BUTTON = auto()
    # TOOL_BUTTON = auto()
    # Categorical
    COMBO_BOX = auto()
    # Dates
    DATE_TIME_EDIT = auto()
    TIME_EDIT = auto()
    DATE_EDIT = auto()
    # Paths
    FILE_EDIT = auto()

    @property
    def snake_name(self):
        """Return snake_case version of the name."""
        return camel2snake(self.value)


WidgetRef = Union[WidgetKind]
TypeMatcher = Callable[[Any, Optional[Type], Optional[dict]], Optional[WidgetRef]]
_TYPE_MATCHERS: Set[TypeMatcher] = set()


def type_matcher(func: TypeMatcher) -> TypeMatcher:
    """Add function to the set of type matchers."""
    _TYPE_MATCHERS.add(func)
    return func


@type_matcher
def sequence_of_paths(value, annotation, options) -> Optional[WidgetRef]:
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
def simple_type(value, annotation, options) -> Optional[WidgetRef]:
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
) -> Optional[WidgetRef]:
    """Pick the appropriate magicgui widget type for ``value`` with ``annotation``."""
    if "widget_type" in options:
        return WidgetRef(options["widget_type"])

    dtype = (get_origin(annotation) or annotation) if annotation else type(value)

    if isinstance(dtype, EnumMeta) or "choices" in options:
        return WidgetKind.COMBO_BOX

    for matcher in _TYPE_MATCHERS:
        widget_type = matcher(value, annotation, options)
        if widget_type:
            return widget_type
    return None


def _get_backend_widget(value, annotation, options, app: AppRef) -> Type[BaseWidget]:
    widget_type = pick_widget_type(value, annotation, options)
    if widget_type is None:
        raise ValueError(
            f"Could not determine widget type for value={value!r}, "
            f"annotation={annotation!r}, options={options}, app={app}"
        )
    _app = use_app(app)
    try:
        return _app.get_obj(widget_type.value)
    except AttributeError as e:
        raise MissingWidget(
            f"Could not find an implementation of widget type {widget_type!r} "
            f"in backend {_app.backend_name!r}\n"
            f"Looked in: {_app.backend_module!r}"
        ) from e
