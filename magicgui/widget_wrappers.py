"""magicgui Widget class that wraps all backend widgets."""
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
from magicgui.events import EventEmitter
from magicgui.protocols import (
    ButtonWidgetProtocol,
    CategoricalWidgetProtocol,
    ContainerProtocol,
    RangedWidgetProtocol,
    SliderWidgetProtocol,
    ValueWidgetProtocol,
    WidgetProtocol,
)
from magicgui.type_map import get_widget_class

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
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = None,
        annotation: Any = None,
        gui_only=False,
        widget_type: Union[str, Type[WidgetProtocol], None] = None,
        app=None,
        **options,
    ):

        kwargs = locals()
        kwargs.pop("widget_type")
        _app = use_app(kwargs.pop("app"))
        assert _app.native
        if isinstance(widget_type, WidgetProtocol):
            wdg_class = widget_type
        else:
            wdg_class = get_widget_class(default, annotation, options)
            if inspect.isclass(wdg_class) and issubclass(wdg_class, Widget):
                kwargs.update(kwargs.pop("options"))
                return wdg_class(**kwargs)

        # pick the appropriate subclass for the given protocol
        # order matters
        for p in ("Categorical", "Ranged", "Button", "Value", ""):
            prot = getattr(protocols, f"{p}WidgetProtocol")
            if isinstance(wdg_class, prot):
                return globals()[f"{p}Widget"](
                    widget_type=wdg_class, **kwargs, **kwargs.pop("options")
                )

        raise TypeError(f"{wdg_class!r} does not implement any known widget protocols")

    def __init__(
        self,
        widget_type: Union[str, Type[WidgetProtocol]],
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = None,
        annotation: Any = None,
        gui_only=False,
    ):
        _widget_type: Type[WidgetProtocol] = self._resolve_widget(widget_type)
        self._widget = _widget_type()

        self.name: str = name
        self.annotation: Any = annotation
        self.kind: inspect._ParameterKind = inspect._ParameterKind[kind.upper()]
        self.gui_only = gui_only
        self.visible: bool = True

        # put the magicgui widget on the native object...may cause error on some backend
        self.native._magic_widget = self
        self._post_init()

        self.default = default

    @classmethod
    def _resolve_widget(
        cls, widget_type: Union[str, Type[WidgetProtocol]]
    ) -> Type[WidgetProtocol]:
        if isinstance(widget_type, str):
            app = use_app()
            assert app.native
            _widget_type = app.get_obj(widget_type)
        else:
            _widget_type = widget_type

        prot = getattr(protocols, cls.__annotations__["_widget"].__name__)
        if not isinstance(_widget_type, prot):
            raise TypeError("{widget_type} does not implement the proper protocol")
        return _widget_type

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

    _widget: ValueWidgetProtocol
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

    _widget: ButtonWidgetProtocol
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

    _widget: RangedWidgetProtocol

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

    _widget: SliderWidgetProtocol

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

    _widget: CategoricalWidgetProtocol

    def __init__(self, choices: ChoicesType = (), **kwargs):
        self._default_choices = choices
        super().__init__(**kwargs)

    def _post_init(self):
        super()._post_init()
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
    def from_signature(cls, sig: Signature, **kwargs) -> "Container":
        from magicgui.signature import MagicSignature

        return MagicSignature.from_signature(sig).to_container(**kwargs)

    @classmethod
    def from_callable(
        cls, obj: Callable, gui_options: Optional[dict] = None, **kwargs
    ) -> "Container":
        from magicgui.signature import magic_signature

        return magic_signature(obj, gui_options=gui_options).to_container(**kwargs)

    def to_signature(self) -> "MagicSignature":
        from magicgui.signature import MagicParameter, MagicSignature

        params = [
            MagicParameter.from_widget(w) for w in self if w.name and not w.gui_only
        ]
        return MagicSignature(params, return_annotation=self._return_annotation)

    def __repr__(self) -> str:
        return f"<Container {self.to_signature()}>"
