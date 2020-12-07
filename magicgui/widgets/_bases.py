"""This module declares Widget base classes.

All magicgui ``Widget`` bases compose a backend widget that implements one of the
widget protocols defined in ``magicgui.widgets._protocols``.

```
class Widget:
    _widget: protocols.WidgetProtocol

    def __init__(self, widget_type: Type[protocols.WidgetProtocol]):
        self._widget = widget_type() # instantiation of the backend widget.
```

These widgets are unlikely to be instantiated directly, (unless you're creating a custom
widget that implements one of the WidgetProtocols... as the backed widgets do).
Instead, one will usually instantiate the widgets in `magicgui.widgets._concrete`...
which are all available direcly in the `magicgui.widgets` namespace.

The one exception is the ``Widget.create`` factory method, which may be used to create
a widget subclass appropriate for the arguments passed (such as "default" or
"annotation").


Main Widget Types
-----------------

Widget (wraps WidgetProtocol)
├── ↪ ValueWidget (wraps ValueWidgetProtocol)
│   ├── Label
│   ├── LineEdit
│   ├── TextEdit
│   ├── DateTimeEdit
│   ├── ↪ ButtonWidget (wraps ButtonWidgetProtocol)
│   │   ├── PushButton
│   │   ├── CheckBox
│   │   └── RadioButton
│   ├── ↪ RangedWidget (wraps RangedWidgetProtocol)
│   │   ├── SpinBox
│   │   ├── FloatSpinBox
│   │   └── ↪ SliderWidget (wraps SliderWidgetProtocol)
│   │       ├── Slider
│   │       └── FloatSlider
│   └── ↪ CategoricalWidget (wraps CategoricalWidgetProtocol)
│       └── ComboBox
└── ↪ ContainerWidget (wraps ContainerProtocol)/
    └── Container

"""
import inspect
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import EnumMeta
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    overload,
)

from magicgui.application import use_app
from magicgui.events import EventEmitter
from magicgui.signature import MagicParameter, MagicSignature, magic_signature
from magicgui.types import ChoicesType, WidgetOptions
from magicgui.widgets import _protocols as protocols

if TYPE_CHECKING:
    from ._concrete import Container


class Widget:
    """Basic Widget, wrapping a class that implements WidgetProtocol.

    Parameters
    ----------
    widget_type : Type[WidgetProtocol]
        A class implementing a widget protocol.  Will be instantiated during __init__.
    name : str, optional
        The name of the parameter represented by this widget. by default ""
    kind : str, optional
        The ``inspect._ParameterKind`` represented by this widget.  Used in building
        signatures from multiple widgets, by default "POSITIONAL_OR_KEYWORD"
    default : Any, optional
        The default & starting value for the widget, by default None
    annotation : Any, optional
        The type annotation for the parameter represented by the widget, by default None
    label : str
        A string to use for an associated Label widget (if this widget is being shown in
        a `Container` widget, and labels are on).  By default, `name` will be used.
        Note: `name` refers the name of the parameter, as might be used in a signature,
        whereas label is just the label for that widget in the GUI.
    gui_only : bool, optional
        Whether the widget should be considered "only for the gui", or if it should be
        included in any widget container signatures, by default False
    """

    _widget: protocols.WidgetProtocol

    def __init__(
        self,
        widget_type: Type[protocols.WidgetProtocol],
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = None,
        annotation: Any = None,
        label=None,
        visible: bool = True,
        gui_only=False,
    ):
        prot = getattr(protocols, self.__class__.__annotations__["_widget"].__name__)
        if not isinstance(widget_type, prot):
            raise TypeError(f"{widget_type!r} does not implement the proper protocol")
        self.__magicgui_app__ = use_app()
        assert self.__magicgui_app__.native
        self._widget = widget_type()
        self.name: str = name
        self.kind: inspect._ParameterKind = inspect._ParameterKind[kind.upper()]
        self.default = default
        self._label = label
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
        if not visible:
            self.hide()

    @staticmethod
    def create(
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = None,
        annotation: Any = None,
        label=None,
        gui_only=False,
        app=None,
        widget_type: Union[str, Type[protocols.WidgetProtocol], None] = None,
        options: WidgetOptions = dict(),
    ):
        kwargs = locals()
        _app = use_app(kwargs.pop("app"))
        assert _app.native
        if isinstance(widget_type, protocols.WidgetProtocol):
            wdg_class = widget_type
        else:
            from magicgui.type_map import get_widget_class

            if widget_type:
                options["widget_type"] = widget_type
            wdg_class, opts = get_widget_class(default, annotation, options)

            if issubclass(wdg_class, Widget):
                opts.update(kwargs.pop("options"))
                kwargs.update(opts)
                kwargs.pop("widget_type", None)
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

    def _post_init(self):
        pass

    @property
    def options(self) -> dict:
        # return {"enabled": self.enabled, "visible": self.visible}
        return {"visible": self.visible}

    @property
    def native(self):
        """Return native backend widget."""
        return self._widget._mg_get_native_widget()

    def show(self, run=False):
        """Show the widget."""
        self._widget._mg_show_widget()
        self.visible = True
        if run:
            self.__magicgui_app__.run()

    @contextmanager
    def shown(self):
        """Context manager to show the widget."""
        try:
            self.show()
            yield self.__magicgui_app__.__enter__()
        finally:
            self.__magicgui_app__.__exit__()

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

    @property
    def label(self):
        return self.name if self._label is None else self._label

    @label.setter
    def label(self, value):
        self._label = value


class ValueWidget(Widget):
    """Widget with a value, Wraps ValueWidgetProtocol."""

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
    """Widget with a value, Wraps ButtonWidgetProtocol.

    Parameters
    ----------
    text : str, optional
        The text to display on the button. If not provided, will use `name`.
    """

    _widget: protocols.ButtonWidgetProtocol
    changed: EventEmitter

    def __init__(self, text: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.text = text or self.name

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
    """Widget with a contstrained value. Wraps RangedWidgetProtocol.

    Parameters
    ----------
    minimum : float, optional
        The minimum allowable value, by default 0
    maximum : float, optional
        The maximum allowable value, by default 100
    step : float, optional
        The step size for incrementing the value, by default 1
    """

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


class TransformedRangedWidget(RangedWidget, ABC):
    """Widget with a contstrained value. Wraps RangedWidgetProtocol.

    This can be used to map one domain of numbers onto another, useful for creating
    things like LogSliders.  Subclasses must reimplement `_value_from_position` and
    `_position_from_value`.

    Parameters
    ----------
    minimum : float, optional
        The minimum allowable value, by default 0
    maximum : float, optional
        The maximum allowable value, by default 100
    min_pos : float, optional
        The minimum value for the *internal* (widget) position, by default 0.
    max_pos : float, optional
        The maximum value for the *internal* (widget) position, by default 0.
    step : float, optional
        The step size for incrementing the value, by default 1
    """

    _widget: protocols.RangedWidgetProtocol

    def __init__(
        self,
        minimum: float = 0,
        maximum: float = 100,
        min_pos: int = 0,
        max_pos: int = 100,
        step: int = 1,
        **kwargs,
    ):
        self._minimum = minimum
        self._maximum = maximum
        self._min_pos = min_pos
        self._max_pos = max_pos
        ValueWidget.__init__(self, **kwargs)

        self._widget._mg_set_minimum(self._min_pos)
        self._widget._mg_set_maximum(self._max_pos)
        self._widget._mg_set_step(step)

    # Just a linear scaling example.
    # Replace _value_from_position, and _position_from_value in subclasses
    # to implement more complex value->position lookups
    @property
    def _scale(self):
        """Slope of a linear map.  Just used as an example."""
        return (self.maximum - self.minimum) / (self._max_pos - self._min_pos)

    @abstractmethod
    def _value_from_position(self, position):
        """Return 'real' value given internal widget position."""
        return self.minimum + self._scale * (position - self._min_pos)

    @abstractmethod
    def _position_from_value(self, value):
        """Return internal widget position given 'real' value."""
        return (value - self.minimum) / self._scale + self._min_pos

    #########

    @property
    def value(self):
        """Return current value of the widget."""
        return self._value_from_position(self._widget._mg_get_value())

    @value.setter
    def value(self, value):
        return self._widget._mg_set_value(self._position_from_value(value))

    @property
    def minimum(self) -> float:
        """Minimum allowable value for the widget."""
        return self._minimum

    @minimum.setter
    def minimum(self, value: float):
        prev = self.value
        self._minimum = value
        self.value = prev

    @property
    def maximum(self) -> float:
        """Maximum allowable value for the widget."""
        return self._maximum

    @maximum.setter
    def maximum(self, value: float):
        prev = self.value
        self._maximum = value
        self.value = prev


class SliderWidget(RangedWidget):
    """Widget with a contstrained value and orientation. Wraps SliderWidgetProtocol.

    Parameters
    ----------
    orientation : str, {'horizontal', 'vertical'}
        The orientation for the slider, by default "horizontal"
    """

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
    """Widget with a value and choices, Wraps CategoricalWidgetProtocol.

    Parameters
    ----------
    choices : Enum, Iterable, or Callable
        Available choices displayed in the combo box.
    """

    _widget: protocols.CategoricalWidgetProtocol

    def __init__(self, choices: ChoicesType = (), **kwargs):
        self._default_choices = choices
        super().__init__(**kwargs)

    def _post_init(self):
        super()._post_init()
        self.reset_choices()
        self.parent_changed.connect(self.reset_choices)

    @property
    def value(self):
        return self._widget._mg_get_value()

    @value.setter
    def value(self, value):
        if value not in self.choices:
            raise ValueError(
                f"{value!r} is not a valid choice. must be in {self.choices}"
            )
        return self._widget._mg_set_value(value)

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
        return tuple(i[1] for i in self._widget._mg_get_choices())

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
            try:
                _choices = choices(self)
            except TypeError:
                import warnings

                n_params = len(inspect.signature(choices).parameters)
                if n_params > 1:
                    warnings.warn(
                        "\nAs of magicgui 0.2.0, a `choices` callable may accept only "
                        "a single positional\nargument (an instance of "
                        "`magicgui.widgets.CategoricalWidget`), and must return\nan "
                        f"iterable (the choices to show). Function {choices.__name__!r}"
                        f" accepts {n_params} arguments.\n"
                        "In the future, this will raise an exception.",
                        DeprecationWarning,
                    )
                    # pre 0.2.0 API
                    _choices = choices(self.native, self.annotation)  # type: ignore
                else:
                    raise
        else:
            _choices = choices
        if not all(isinstance(i, tuple) and len(i) == 2 for i in _choices):
            _choices = [(str_func(i), i) for i in _choices]
        return self._widget._mg_set_choices(_choices)


class ContainerWidget(Widget, MutableSequence[Widget]):
    """Widget that can contain other widgets. Wraps ContainerProtocol.

    A container widget behaves like a python list of Widget objects.
    Subwidgets can be accessed using integer or slice-based indexing (`container[0]`),
    as well as by widget name (`container.<widget_name>`). Widgets can be
    added with `append` or `insert`, and removed with `del` or `pop`, etc...

    There is a tight connection between a ``ContainerWidget`` and an
    ``inspect.Signature`` object, just as there is a tight connection between individual
    widget objects an an ``inspect.Parameter`` object.  The signature representation of
    a ``ContainerWidget`` (with the current settings as default values) is accessible
    with the ``to_signature()`` method.

    For a ``ContainerWidget`` sublcass that is tightly coupled to a specific function
    signature (as in the "classic" magicgui decorator), see ``magicgui.FunctionGui``.

    Parameters
    ----------
    orientation : str, optional
        The orientation for the container.  must be one of {'horizontal', 'vertical'}.
        by default "horizontal"
    widgets : Sequence[Widget], optional
        A sequence of widgets with which to intialize the container, by default None.
    labels : bool, optional
        Whethter each widget should be shown with a corresponding Label widget to the
        left, by default True.  Note: the text for each widget defaults to
        ``widget.name``, but can be overriden by setting ``widget.label``.
    return_annotation : Type or str, optional
        An optional return annotation to use when representing this container of
        widgets as an inspect.Signature, by default None
    """

    changed: EventEmitter
    _widget: protocols.ContainerProtocol
    _initialized = False

    def __init__(
        self,
        orientation: str = "horizontal",
        widgets: Sequence[Widget] = (),
        labels=True,
        return_annotation: Any = None,
        **kwargs,
    ):
        self.labels = labels
        super().__init__(**kwargs)
        self.changed = EventEmitter(source=self, type="changed")
        self._return_annotation = return_annotation
        for w in widgets:
            self.append(w)
        self._initialized = True

    def __getattr__(self, name: str):
        for widget in self:
            if name == widget.name:
                return widget
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any):
        if self._initialized:
            for widget in self:
                if name == widget.name:
                    raise AttributeError(
                        "Cannot set attribute with same name as a widget\n"
                        "If you are trying to change the value of a widget, use: "
                        f"`{self.__class__.__name__}.{name}.value = {value}`",
                    )
        object.__setattr__(self, name, value)

    @overload
    def __getitem__(self, key: Union[int, str]) -> Widget:
        ...

    @overload
    def __getitem__(self, key: slice) -> MutableSequence[Widget]:  # noqa: F811
        ...

    def __getitem__(self, key):  # noqa: F811
        if isinstance(key, str):
            return self.__getattr__(key)
        if isinstance(key, slice):
            out = []
            for idx in range(*key.indices(len(self))):
                item = self._widget._mg_get_index(idx)
                if item:
                    out.append(item)
            return out
        elif isinstance(key, int):
            if key < 0:
                key += len(self)
        item = self._widget._mg_get_index(key)
        if not item:
            raise IndexError("Container index out of range")
        return item

    def index(self, value: Any, start=0, stop=9223372036854775807) -> int:
        if isinstance(value, str):
            value = getattr(self, value)
        return super().index(value, start, stop)

    def remove(self, value: Union[Widget, str]):
        super().remove(value)  # type: ignore

    def __delattr__(self, name: str):
        self.remove(name)

    def __delitem__(self, key: Union[int, slice]):
        if isinstance(key, slice):
            for idx in range(*key.indices(len(self))):
                self._widget._mg_remove_index(idx)
        else:
            if key < 0:
                key += len(self)
            self._widget._mg_remove_index(key)

    def __len__(self) -> int:
        return self._widget._mg_count()

    def __setitem__(self, key, value):
        raise NotImplementedError("magicgui.Container does not support item setting.")

    def __dir__(self) -> List[str]:
        d = list(super().__dir__())
        d.extend([w.name for w in self if not w.gui_only])
        return d

    def insert(self, key: int, widget: Widget):
        if isinstance(widget, ValueWidget):
            widget.changed.connect(lambda x: self.changed(value=self))
        self._widget._mg_insert_widget(key, widget)
        if self.labels:
            # no labels for button widgets (push buttons, checkboxes, have their own)
            if isinstance(widget, ButtonWidget):
                return
            label = Widget.create(widget_type="Label", default=widget.label)
            self._widget._mg_insert_widget(key, label)

    @property
    def native_layout(self):
        return self._widget._mg_get_native_layout()

    @classmethod
    def from_signature(cls, sig: inspect.Signature, **kwargs) -> "Container":
        return MagicSignature.from_signature(sig).to_container(**kwargs)

    @classmethod
    def from_callable(
        cls, obj: Callable, gui_options: Optional[dict] = None, **kwargs
    ) -> "Container":
        return magic_signature(obj, gui_options=gui_options).to_container(**kwargs)

    @property
    def __signature__(self) -> inspect.Signature:
        """Return signature object, for compatibility with inspect.signature()."""
        return self.to_signature()

    def reset_choices(self, event=None):
        for widget in self:
            if isinstance(widget, CategoricalWidget):
                widget.reset_choices()

    def refresh_choices(self, event=None):
        import warnings

        warnings.warn(
            "\n`ContainerWidget.refresh_choices` is deprecated and will be removed in a"
            " future version, please use `ContainerWidget.reset_choices` instead.",
            FutureWarning,
        )
        return self.reset_choices(event)

    def to_signature(self) -> "MagicSignature":
        params = [
            MagicParameter.from_widget(w) for w in self if w.name and not w.gui_only
        ]
        return MagicSignature(params, return_annotation=self._return_annotation)

    def __repr__(self) -> str:
        return f"<Container {self.to_signature()}>"
