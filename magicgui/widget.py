"""magicgui Widget class that wraps all backend widgets."""
import inspect
from enum import EnumMeta
from typing import Any, Callable, Iterable, Optional, Set, Tuple, Type, TypedDict, Union

from magicgui.application import AppRef, use_app
from magicgui.base import (
    BaseCategoricalWidget,
    BaseRangedWidget,
    BaseValueWidget,
    BaseWidget,
    SupportsChoices,
)
from magicgui.event import EventEmitter
from magicgui.type_map import _get_backend_widget

WidgetRef = Optional[str]
TypeMatcher = Callable[[Any, Optional[Type], Optional[dict]], WidgetRef]
_TYPE_MATCHERS: Set[TypeMatcher] = set()
ChoicesIterable = Union[Iterable[Tuple[str, Any]], Iterable[Any]]
ChoicesCallback = Callable[["CategoricalWidget"], ChoicesIterable]
ChoicesType = Union[EnumMeta, ChoicesIterable, ChoicesCallback, "ChoicesDict"]


class ChoicesDict(TypedDict):
    """Dict Type for setting choices in a categorical widget."""

    choices: ChoicesIterable
    key: Callable[[Any], str]


class Widget:
    """Basic Widget, wrapping the BaseWidget protocol."""

    _widget: BaseWidget

    @staticmethod
    def create(
        value: Any = None,
        annotation=None,
        options: dict = {},
        name: Optional[str] = None,
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        app: AppRef = None,
        gui_only=False,
    ):
        """Widget factory. All widgets should be created with this method."""
        # Make sure that the app is active
        kwargs = locals().copy()
        _app = use_app(kwargs.pop("app"))
        wdg_class = _get_backend_widget(value, annotation, options, app)
        assert _app.native
        kwargs["wdg_class"] = wdg_class
        if isinstance(wdg_class, BaseCategoricalWidget):
            return CategoricalWidget(**kwargs)
        if isinstance(wdg_class, BaseRangedWidget):
            return RangedWidget(**kwargs)
        if isinstance(wdg_class, BaseValueWidget):
            return ValueWidget(**kwargs)
        return Widget(**kwargs)

    def __init__(
        self,
        wdg_class: Type[BaseWidget],
        name: Optional[str] = None,
        value: Any = None,
        annotation=None,
        options: dict = {},
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        gui_only=False,
    ):
        self.name = name
        self.default = value
        self.annotation = annotation
        self._options = options
        self._kind = kind
        self.gui_only = gui_only

        self._widget = wdg_class()
        # put the magicgui widget on the native object...may cause error on some backend
        self.native._magic_widget = self

        self._post_init()
        if self.default:
            self.value = self.default

    def _post_init(self):
        """For subclasses, so they don't have to recreate init signature."""
        pass

    @property
    def is_mandatory(self) -> bool:
        """Whether the parameter represented by this widget is mandatory."""
        if self._kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        ):
            return self.default is inspect.Parameter.empty
        return False

    @property
    def native(self):
        """Return native backend widget."""
        return self._widget._mg_get_native_widget()

    def show(self):
        """Show widget."""
        self._widget._mg_show_widget()

    def hide(self):
        """Hide widget."""
        self._widget._mg_hide_widget()

    @property
    def widget_type(self) -> str:
        """Return type of widget."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        return (
            f"Widget(value={self.value!r}, annotation={self.annotation!r}, "
            f"options={self._options}, name={self.name!r}, kind={self._kind})"
        )


class ValueWidget(Widget):
    """Widget with a value, wrapping the BaseValueWidget protocol."""

    _widget: BaseValueWidget
    changed: EventEmitter

    def _post_init(self):
        super()._post_init()
        self.changed = EventEmitter(source=self, type="changed")
        # TODO: fix this pattern
        self._widget._mg_bind_change_callback(lambda x: self.changed(value=x))

    @property
    def value(self):
        """Return current value of the widget.  This may be interpreted by backends."""
        return self._widget._mg_get_value()

    @value.setter
    def value(self, value):
        return self._widget._mg_set_value(value)


class RangedWidget(ValueWidget):
    """Widget with a contstrained value wraps BaseRangedWidget protocol."""

    _widget: BaseRangedWidget

    @property
    def minimum(self) -> float:
        """Minimum allowable value for the widget."""
        return self._widget._mg_get_minimum()

    @minimum.setter
    def minimum(self, value: float):
        self._widget._mg_set_minimum(value)

    @property
    def maximum(self) -> float:
        """Maximum allowable value for the widget."""
        return self._widget._mg_get_maximum()

    @maximum.setter
    def maximum(self, value: float):
        self._widget._mg_set_maximum(value)

    @property
    def step(self) -> float:
        """Step size for widget values."""
        return self._widget._mg_get_step()

    @step.setter
    def step(self, value: float):
        self._widget._mg_set_step(value)

    @property
    def range(self) -> Tuple[float, float]:
        """Range of allowable values for the widget."""
        return self._widget._mg_get_range()

    @range.setter
    def range(self, value: Tuple[float, float]):
        self._widget._mg_set_range(value)


class CategoricalWidget(ValueWidget):
    """Widget with a value and choices, wrapping the BaseCategoricalWidget protocol."""

    _widget: BaseCategoricalWidget

    def _post_init(self):
        super()._post_init()
        self._default_choices = self._options.get("choices")
        if not isinstance(self._widget, SupportsChoices):
            raise ValueError(f"widget {self._widget!r} does not support 'choices'")
        self.reset_choices()

    def reset_choices(self):
        """Reset choices to the default state.

        If self._default_choices is a callable, this may NOT be the exact same set of
        choices as when the widget was instantiated, if the callable relies on external
        state.
        """
        self.choices = self._default_choices

    @property
    def choices(self):
        """Available value choices for this widget."""
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
