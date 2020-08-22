"""magicgui Widget class that wraps all backend widgets."""
import inspect
from enum import EnumMeta
from inspect import Signature
from typing import (
    Any,
    Callable,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    overload,
)

from magicgui import protocols
from magicgui.application import use_app
from magicgui.events import EventEmitter
from magicgui.signature import MagicParameter, MagicSignature, magic_signature
from magicgui.types import ChoicesType, WidgetOptions

# -> WidgetProtocol
#      ↪ ValueWidgetProtocol
#           ↪ RangedWidgetProtocol
#                ↪ SliderWidgetProtocol (+ SupportsOrientation)
#           ↪ ButtonWidgetProtocol (+ SupportsText)
#           ↪ CategoricalWidgetProtocol
#      ↪ ContainerProtocol (+ SupportsOrientation)


class Widget:
    """Basic Widget, wrapping a class that implements WidgetProtocol."""

    _widget: protocols.WidgetProtocol

    @staticmethod
    def create(
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = None,
        annotation: Any = None,
        gui_only=False,
        app=None,
        widget_type: Union[str, Type[protocols.WidgetProtocol], None] = None,
        options: WidgetOptions = dict(),
    ):
        _app = use_app(app)
        assert _app.native
        if not isinstance(widget_type, protocols.WidgetProtocol):
            from magicgui.type_map import get_widget_class

            if widget_type:
                options["widget_type"] = widget_type
            wdg_class, opts = get_widget_class(default, annotation, options)
            if issubclass(wdg_class, Widget):
                opts.update(options)
                return wdg_class(**opts)  # type: ignore
            options.pop("widget_type", None)
        else:
            wdg_class = widget_type

        # pick the appropriate subclass for the given protocol
        # order matters
        for p in ("Categorical", "Ranged", "Button", "Value", ""):
            prot = getattr(protocols, f"{p}WidgetProtocol")
            if isinstance(wdg_class, prot):
                return globals()[f"{p}Widget"](widget_type=wdg_class, **options)

        raise TypeError(f"{wdg_class!r} does not implement any known widget protocols")

    def __init__(
        self,
        widget_type: Type[protocols.WidgetProtocol],
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = None,
        annotation: Any = None,
        gui_only=False,
    ):
        prot = getattr(protocols, self.__class__.__annotations__["_widget"].__name__)
        if not isinstance(widget_type, prot):
            raise TypeError(f"{widget_type!r} does not implement the proper protocol")
        self._widget = widget_type()

        self.name: str = name
        self.kind: inspect._ParameterKind = inspect._ParameterKind[kind.upper()]
        self.default = default
        self.annotation: Any = annotation
        self.gui_only = gui_only
        self.visible: bool = True
        self.parent_changed = EventEmitter(source=self, type="parent_changed")
        self._widget._mg_bind_parent_change_callback(
            lambda *x: self.parent_changed(value=self.parent)
        )

        # put the magicgui widget on the native object...may cause error on some backend
        self.native._magic_widget = self
        self._post_init()

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
    def parent(self) -> "Widget":
        return self._widget._mg_get_parent()

    @parent.setter
    def parent(self, value: "Widget"):
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

    _widget: protocols.ValueWidgetProtocol
    changed: EventEmitter

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.default is not None:
            self.value = self.default

    def _post_init(self):
        super()._post_init()
        self.changed = EventEmitter(source=self, type="changed")
        self._widget._mg_bind_change_callback(
            lambda *x: self.changed(value=x[0] if x else None)
        )

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
            f"{self.widget_type}(value={self.value!r}, annotation={self.annotation!r}, "
            f"name={self.name!r})"
        )


class ButtonWidget(ValueWidget):
    """Widget with a value, wrapping the BaseValueWidget protocol."""

    _widget: protocols.ButtonWidgetProtocol
    changed: EventEmitter

    def __init__(self, text: str = "Text", **kwargs):
        super().__init__(**kwargs)
        self.text = text

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

    _widget: protocols.RangedWidgetProtocol

    def __init__(
        self, minimum: float = 0, maximum: float = 100, step: float = 1, **kwargs
    ):
        super().__init__(**kwargs)

        self.minimum = minimum
        self.maximum = maximum
        self.step = step

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


class SliderWidget(RangedWidget):

    _widget: protocols.SliderWidgetProtocol

    def __init__(self, orientation: str = "horizontal", **kwargs):
        super().__init__(**kwargs)

        self.orientation = orientation

    @property
    def options(self) -> dict:
        d = super().options.copy()
        d.update({"orientation": self.orientation})
        return d


class CategoricalWidget(ValueWidget):
    """Widget with a value and choices, wrapping the BaseCategoricalWidget protocol."""

    _widget: protocols.CategoricalWidgetProtocol

    def __init__(self, choices: ChoicesType = (), **kwargs):
        self._default_choices = choices
        super().__init__(**kwargs)

    def _post_init(self):
        super()._post_init()
        self.reset_choices()
        self.parent_changed.connect(self.reset_choices)

    @property
    def options(self) -> dict:
        d = super().options.copy()
        d.update({"choices": self._default_choices})
        return d

    def reset_choices(self, event=None):
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
    _widget: protocols.ContainerProtocol

    def __init__(
        self,
        orientation: str = "horizontal",
        widgets: Sequence[Widget] = (),
        return_annotation: Any = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.changed = EventEmitter(source=self, type="changed")
        self._return_annotation = return_annotation
        for w in widgets:
            self.append(w)

    def __getattr__(self, name: str):
        for widget in self:
            if name == widget.name:
                return widget
        return object.__getattribute__(self, name)

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
    def from_signature(cls, sig: Signature, **kwargs) -> "Container":
        return MagicSignature.from_signature(sig).to_container(**kwargs)

    @classmethod
    def from_callable(
        cls, obj: Callable, gui_options: Optional[dict] = None, **kwargs
    ) -> "Container":
        return magic_signature(obj, gui_options=gui_options).to_container(**kwargs)

    def to_signature(self) -> "MagicSignature":
        params = [
            MagicParameter.from_widget(w) for w in self if w.name and not w.gui_only
        ]
        return MagicSignature(params, return_annotation=self._return_annotation)

    def __repr__(self) -> str:
        return f"<Container {self.to_signature()}>"
