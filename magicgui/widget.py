"""magicgui Widget class that wraps all backend widgets."""
import datetime
import inspect
import pathlib
from collections import abc
from enum import EnumMeta
from typing import Any, Callable, Optional, Set, Type, Union, Iterable, Tuple, TypedDict

from typing_extensions import get_args, get_origin  # type: ignore

from .application import AppRef, use_app
from .base import BaseWidget, BaseCategoricalWidget, SupportsChoices

WidgetRef = Optional[str]
TypeMatcher = Callable[[Any, Optional[Type], Optional[dict]], WidgetRef]
_TYPE_MATCHERS: Set[TypeMatcher] = set()


def type_matcher(func: TypeMatcher) -> TypeMatcher:
    """Add function to the set of type matchers."""
    _TYPE_MATCHERS.add(func)
    return func


@type_matcher
def sequence_of_paths(value, annotation, options):
    """Determine if value/annotation is a Sequence[pathlib.Path]."""

    def is_path(v):
        return

    if annotation:
        orig = get_origin(annotation)
        args = get_args(annotation)
        if not (inspect.isclass(orig) and args):
            return
        if issubclass(orig, abc.Sequence):
            if inspect.isclass(args[0]) and issubclass(args[0], pathlib.Path):
                return "FilesDialog"
    elif value:
        if isinstance(value, abc.Sequence) and all(
            isinstance(v, pathlib.Path) for v in value
        ):
            return "FilesDialog"


@type_matcher
def simple_type(value, annotation, options):
    """Check simple type mappings."""
    dtype = (get_origin(annotation) or annotation) if annotation else type(value)

    simple = {
        bool: "CheckBox",
        int: "SpinBox",
        float: "FloatSpinBox",
        str: "LineEdit",
        pathlib.Path: "FileDialog",
        datetime.datetime: "DateTimeEdit",
        type(None): "LineEdit",
    }
    if dtype in simple:
        return simple[dtype]
    else:
        for key in simple.keys():
            if inspect.isclass(dtype) and issubclass(dtype, key):
                return simple[key]


def pick_widget_type(
    value: Any = None, annotation: Optional[Type] = None, options: dict = {},
) -> Optional[str]:
    """Pick the appropriate magicgui widget type for ``value`` with ``annotation``."""
    if "widget_type" in options:
        return options["widget_type"]

    dtype = (get_origin(annotation) or annotation) if annotation else type(value)

    if isinstance(dtype, EnumMeta) or "choices" in options:
        return "ComboBox"

    for matcher in _TYPE_MATCHERS:
        widget_type = matcher(value, annotation, options)
        if widget_type:
            return widget_type
    return None


class MissingWidget(Exception):
    pass


class InvalidOption(Exception):
    pass


class SignalConnector:
    def __init__(self, connector: Callable):
        self.connector = connector

    def connect(self, callback: Callable[[Any], None]):
        self.connector(callback)


class Widget:
    _widget: BaseWidget
    value_changed: SignalConnector

    def __new__(cls, *args, **kwargs):
        # FIXME: Works... but ugly?
        if cls is Widget and kwargs.get("options", {}).get("choices"):
            return super().__new__(CategoricalWidget)
        return super().__new__(cls)

    def __init__(
        self,
        value: Any = None,
        annotation=None,
        options: dict = {},
        name: str = "",
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        app: AppRef = None,
    ):
        # Make sure that the app is active
        _app = use_app(app)
        assert _app.native
        self.name = name
        self.annotation = annotation
        self.default = value
        self._kind = kind
        self._options = options
        self._create_native(value, annotation, options, _app)
        if value:
            self.value = value
        self.value_changed = SignalConnector(self._widget._mg_bind_change_callback)

    def _create_native(self, value, annotation, options, _app):
        widget_type = pick_widget_type(value, annotation, options)
        if widget_type is None:
            raise ValueError("Could not determine widget type")
        try:
            # Instantiate the widget with the right class
            backend_widget: Type[BaseWidget] = getattr(_app.backend_module, widget_type)
        except AttributeError:
            raise MissingWidget(
                f"Could not find an implementation of widget type {widget_type!r} "
                f"in backend {_app.backend_name!r}\n"
                f"Looked in: {_app.backend_module!r}"
            )
        self._widget = backend_widget(mg_widget=self)

    @property
    def is_mandatory(self) -> bool:
        if self._kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        ):
            return self.default is inspect.Parameter.empty
        return False

    @property
    def value(self):
        return self._widget._mg_get_value()

    @value.setter
    def value(self, value):
        return self._widget._mg_set_value(value)

    @property
    def native(self):
        return self._widget._mg_get_native_widget()

    def show(self):
        self._widget._mg_show_widget()

    def hide(self):
        self._widget._mg_hide_widget()

    @property
    def widget_type(self) -> str:
        """Return type of widget."""
        return self.__class__.__name__

    # def __repr__(self):
    #     """Return string representation of widget."""
    #     _type = type(self.native)
    #     backend = f"{_type.__module__}.{_type.__qualname__}"
    #     return f"<Magic {self.widget_type} ({backend!r}) at {hex(id(self))}>"

    def __repr__(self) -> str:
        return (
            f"Widget(value={self.value!r}, annotation={self.annotation!r}, "
            f"options={self._options}, name={self.name!r}, kind={self._kind})"
        )


ChoicesIterable = Union[Iterable[Tuple[str, Any]], Iterable[Any]]
ChoicesCallback = Callable[["CategoricalWidget"], ChoicesIterable]


class ChoicesDict(TypedDict):
    choices: ChoicesIterable
    key: Callable[[Any], str]


ChoicesType = Union[EnumMeta, ChoicesIterable, ChoicesCallback, ChoicesDict]


class CategoricalWidget(Widget):
    _widget: BaseCategoricalWidget

    def __init__(self, *args, **kwargs):
        self._default_choices = kwargs.get("options", {}).get("choices")
        super().__init__(*args, **kwargs)

    def _create_native(self, value, annotation, options, _app):
        super()._create_native(value, annotation, options, _app)
        if not isinstance(self._widget, SupportsChoices):
            raise InvalidOption(f"widget {self._widget!r} does not support 'choices'")
        self.reset_choices()

    def reset_choices(self):
        # particularly useful if self._default_choices is a
        self.choices = self._default_choices

    @property
    def choices(self):
        return tuple(i[0] for i in self._widget._mg_get_choices())

    @choices.setter
    def choices(self, choices: ChoicesType):
        if isinstance(choices, EnumMeta):
            str_func: Callable = lambda x: str(x.name)
        else:
            str_func = str
        if isinstance(choices, dict):
            if not ("choices" in choices and "key" in choices):
                raise ValueError(
                    "When setting choices with a dict, the dict must have keys "
                    "'choices' (Iterable), and 'key' (callable that takes a each value "
                    "in `choices` and returns a string."
                )
            _choices = choices["choices"]
            str_func = choices["key"]
        elif not isinstance(choices, EnumMeta) and callable(choices):
            _choices = choices(self)
        else:
            _choices = choices
        if not all(isinstance(i, tuple) and len(i) == 2 for i in _choices):
            _choices = [(str_func(i), i) for i in _choices]
        return self._widget._mg_set_choices(_choices)

    def __repr__(self):
        """Return string representation of widget."""
        _type = type(self.native)
        backend = f"{_type.__module__}.{_type.__qualname__}"
        return f"<MagicCategoricalWidget ({backend!r}) at {hex(id(self))}>"
