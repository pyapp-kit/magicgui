"""magicgui Widget class that wraps all backend widgets."""
from __future__ import annotations

import inspect
from enum import EnumMeta
from inspect import Signature
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    MutableSequence,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypedDict,
    Union,
    overload,
)

from magicgui import protocols
from magicgui.application import use_app
from magicgui.constants import WidgetKind
from magicgui.events import EventEmitter
from magicgui.protocols import (
    ButtonWidgetProtocol,
    CategoricalWidgetProtocol,
    ContainerProtocol,
    RangedWidgetProtocol,
    ValueWidgetProtocol,
    WidgetProtocol,
)
from magicgui.type_map import pick_widget_type

if TYPE_CHECKING:
    from magicgui.signature import MagicSignature


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


# -> WidgetProtocol
#      ↪ ValueWidgetProtocol
#           ↪ RangedWidgetProtocol
#                ↪ SliderWidgetProtocol (+ SupportsOrientation)
#           ↪ ButtonWidgetProtocol (+ SupportsText)
#           ↪ CategoricalWidgetProtocol
#      ↪ ContainerProtocol (+ SupportsOrientation)


class Widget:
    """Basic Widget, wrapping a class that implements WidgetProtocol."""

    _widget: WidgetProtocol

    @staticmethod
    def create(
        name: str = "",
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default: Any = inspect.Parameter.empty,
        annotation: Any = None,
        gui_only=False,
        widget_type: Union[str, Type[WidgetProtocol], None] = None,
        app=None,
        **options,
    ):

        kwargs = locals()
        _app = use_app(kwargs.pop("app"))
        assert _app.native

        if isinstance(widget_type, WidgetProtocol):
            wdg_class = widget_type
        elif isinstance(widget_type, str):
            app = use_app()
            assert app.native
            wdg_class = app.get_obj(widget_type)
        else:
            wdg_class = pick_widget_type(default, annotation, options)
            if not isinstance(wdg_class, WidgetProtocol):
                if isinstance(wdg_class, WidgetKind):
                    wdg_class = wdg_class.value
                app = use_app()
                assert app.native
                wdg_class = app.get_obj(wdg_class)

        # pick the appropriate subclass for the given protocol
        # order matters
        for p in ("Categorical", "Ranged", "Button", "Value", ""):
            prot = getattr(protocols, f"{p}WidgetProtocol")
            if isinstance(wdg_class, prot):
                kwargs["widget_type"] = wdg_class
                return globals()[f"{p}Widget"](**kwargs, **kwargs.pop("options"))

        raise TypeError(f"{wdg_class!r} does not implement any known widget protocols")

    def __init__(
        self,
        widget_type: Type[WidgetProtocol],
        name: str = "",
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default: Any = inspect.Parameter.empty,
        annotation: Any = None,
        gui_only=False,
    ):
        self._instance_check(widget_type)
        self._widget = widget_type()

        self.name: str = name
        self.annotation: Any = annotation
        self.kind: inspect._ParameterKind = kind
        self.gui_only = gui_only
        self.visible: bool = True

        # put the magicgui widget on the native object...may cause error on some backend
        self.native._magic_widget = self
        self._post_init()

        self.default = default
        if default and default is not inspect.Parameter.empty:
            self.value = self.default

    def _instance_check(self, cls):
        assert isinstance(cls, WidgetProtocol)

    def _post_init(self):
        pass

    @property
    def options(self) -> dict:
        return {"enabled": self.enabled, "visible": self.visible}

    @property
    def native(self):
        """Return native backend widget."""
        return self._widget._mg_get_native_widget()

    def show(self):
        """Show widget."""
        self._widget._mg_show_widget()
        self.visible = True

    def hide(self):
        """Hide widget."""
        self._widget._mg_hide_widget()
        self.visible = False

    @property
    def enabled(self) -> bool:
        return self._widget._mg_get_enabled()

    @enabled.setter
    def enabled(self, value: bool):
        self._widget._mg_set_enabled(value)

    @property
    def parent(self) -> Widget:
        return self._widget._mg_get_parent()

    @parent.setter
    def parent(self, value: Widget):
        self._widget._mg_set_parent(value)

    @property
    def widget_type(self) -> str:
        """Return type of widget."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        return f"{self.widget_type}(annotation={self.annotation!r}, name={self.name!r})"


class ValueWidget(Widget):
    """Widget with a value, wrapping the BaseValueWidget protocol."""

    _widget: ValueWidgetProtocol
    changed: EventEmitter

    def _post_init(self):
        self.changed = EventEmitter(source=self, type="changed")
        self._widget._mg_bind_change_callback(
            lambda *x: self.changed(value=x[0] if x else None)
        )

    def _instance_check(self, cls):
        assert isinstance(cls, ValueWidgetProtocol)

    @property
    def value(self):
        """Return current value of the widget.  This may be interpreted by backends."""
        return self._widget._mg_get_value()

    @value.setter
    def value(self, value):
        return self._widget._mg_set_value(value)

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        return (
            f"Widget(value={self.value!r}, annotation={self.annotation!r}, "
            f"name={self.name!r})"
        )


class ButtonWidget(ValueWidget):
    """Widget with a value, wrapping the BaseValueWidget protocol."""

    _widget: ButtonWidgetProtocol
    changed: EventEmitter

    def __init__(
        self,
        widget_type: Union[str, Type[ButtonWidgetProtocol], None],
        name: str = "",
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default: Any = inspect.Parameter.empty,
        annotation=None,
        text: str = "Text",
        gui_only=False,
    ):
        kwargs = locals()
        [kwargs.pop(i) for i in ("self", "__class__", "text")]
        super().__init__(**kwargs)
        self.text = text

    def _instance_check(self, cls):
        assert isinstance(cls, ButtonWidgetProtocol)

    @property
    def options(self) -> dict:
        d = super().options.copy()
        d.update({"text": self.text})
        return d

    @property
    def text(self):
        """Text of the widget."""
        return self._widget._mg_get_text()

    @text.setter
    def text(self, value):
        self._widget._mg_set_text(value)


class RangedWidget(ValueWidget):
    """Widget with a contstrained value wraps BaseRangedWidget protocol."""

    _widget: RangedWidgetProtocol

    def __init__(
        self,
        widget_type: Union[str, Type[RangedWidgetProtocol], None],
        name: str = "",
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default: Any = inspect.Parameter.empty,
        annotation=None,
        minimum: float = 0,
        maximum: float = 100,
        step: float = 1,
        gui_only=False,
    ):
        kwargs = locals()
        [kwargs.pop(i) for i in ("self", "__class__", "minimum", "maximum", "step")]
        super().__init__(**kwargs)

        self.minimum = minimum
        self.maximum = maximum
        self.step = step

    def _instance_check(self, cls):
        assert isinstance(cls, RangedWidgetProtocol)

    @property
    def options(self) -> dict:
        d = super().options.copy()
        d.update({"minimum": self.minimum, "maximum": self.maximum, "step": self.step})
        return d

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
        return self.minimum, self.maximum

    @range.setter
    def range(self, value: Tuple[float, float]):
        self.minimum, self.maximum = value


class CategoricalWidget(ValueWidget):
    """Widget with a value and choices, wrapping the BaseCategoricalWidget protocol."""

    _widget: CategoricalWidgetProtocol

    def __init__(
        self,
        widget_type: Union[str, Type[CategoricalWidgetProtocol], None],
        name: str = "",
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default: Any = inspect.Parameter.empty,
        annotation=None,
        choices: ChoicesType = (),
        gui_only=False,
    ):
        self._default_choices = choices

        kwargs = locals()
        [kwargs.pop(i) for i in ("self", "__class__", "choices")]
        super().__init__(**kwargs)

    def _instance_check(self, cls):
        assert isinstance(cls, CategoricalWidgetProtocol)

    def _post_init(self):
        self.reset_choices()

    @property
    def options(self) -> dict:
        d = super().options.copy()
        d.update({"choices": self._default_choices})
        return d

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


class Container(Widget, MutableSequence[Widget]):
    """Widget that can contain other widgets."""

    changed: EventEmitter
    _widget: ContainerProtocol

    def __init__(
        self,
        widget_type: Union[str, Type[ContainerProtocol], None],
        *,
        orientation="horizontal",
        widgets: Sequence[Widget] = [],
        return_annotation=Signature.empty,
        # stuff for Widget.__init__
        name: str = "",
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default: Any = inspect.Parameter.empty,
        annotation=None,
        gui_only=False,
    ):
        kwargs = locals().copy()
        for i in ("self", "__class__", "orientation", "widgets", "return_annotation"):
            del kwargs[i]
        super().__init__(**kwargs)

        self.changed = EventEmitter(source=self, type="changed")
        self._return_annotation = return_annotation
        for w in widgets:
            self.append(w)

    def __getattr__(self, name: str):
        for widget in self:
            if name == widget.name:
                return widget
        raise AttributeError(f"'Container' object has no attribute {name!r}")

    def __delitem__(self, key: Union[int, slice]):
        if isinstance(key, slice):
            for idx in range(*key.indices(len(self))):
                self._widget._mg_remove_index(idx)
        else:
            self._widget._mg_remove_index(key)

    @overload
    def __getitem__(self, key: int) -> Widget:
        ...

    @overload
    def __getitem__(self, key: slice) -> MutableSequence[Widget]:  # noqa: F811
        ...

    def __getitem__(self, key):  # noqa: F811
        if isinstance(key, slice):
            out = []
            for idx in range(*key.indices(len(self))):
                item = self._widget._mg_get_index(idx)
                if item:
                    out.append(item)
            return out

        item = self._widget._mg_get_index(key)
        if not item:
            raise IndexError("Container index out of range")
        return item

    def __len__(self) -> int:
        return self._widget._mg_count()

    def __setitem__(self, key, value):
        raise NotImplementedError("magicgui.Container does not support item setting.")

    def insert(self, key: int, widget: Widget):
        if isinstance(widget, ValueWidget):
            widget.changed.connect(lambda x: self.changed(value=self))
        self._widget._mg_insert_widget(key, widget)

    @property
    def native_layout(self):
        return self._widget._mg_get_native_layout()

    @classmethod
    def from_signature(cls, sig: Signature, **kwargs) -> Container:
        from magicgui.signature import MagicSignature

        return MagicSignature.from_signature(sig).to_container(**kwargs)

    @classmethod
    def from_callable(
        cls, obj: Callable, gui_options: Optional[dict] = None, **kwargs
    ) -> Container:
        from magicgui.signature import magic_signature

        return magic_signature(obj, gui_options=gui_options).to_container(**kwargs)

    def to_signature(self) -> MagicSignature:
        from magicgui.signature import MagicParameter, MagicSignature

        params = [
            MagicParameter.from_widget(w) for w in self if w.name and not w.gui_only
        ]
        return MagicSignature(params, return_annotation=self._return_annotation)

    def __repr__(self) -> str:
        return f"<Container {self.to_signature()}>"
