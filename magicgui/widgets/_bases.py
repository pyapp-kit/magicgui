"""Widget base classes.

These will rarely be used directly by end-users, instead see the "concrete" widgets
exported in :mod:`magicgui.widgets`.

All magicgui :class:`Widget` bases comprise a backend widget that implements one of the
widget protocols defined in :mod:`magicgui.widgets._protocols`.  The basic composition
pattern is as follows:

.. code-block:: python

   class Widget:

       def __init__(
            self,

            # widget_type is a class, likely from the `backends` module
            # that implements one of the `WidgetProtocols` defined in _protocols.
            widget_type: Type[protocols.WidgetProtocol],

            # backend_kwargs is a key-value map of arguments that will be provided
            # to the concrete (backend) implementation of the WidgetProtocol
            backend_kwargs: dict = dict(),

            # additional kwargs will be provided to the magicgui.Widget itself
            # things like, `name`, `value`, etc...
            **kwargs
        ):
           # instantiation of the backend widget.
           self._widget = widget_type(**backend_kwargs)

           # ... go on to set other kwargs


These widgets are unlikely to be instantiated directly, (unless you're creating a custom
widget that implements one of the WidgetProtocols... as the backed widgets do).
Instead, one will usually instantiate the widgets in :mod:`magicgui.widgets._concrete`
which are all available direcly in the :mod:`magicgui.widgets` namespace.

The :func:`~magicgui.widgets.create_widget` factory function may be used to
create a widget subclass appropriate for the arguments passed (such as "value" or
"annotation").

"""
from __future__ import annotations

import inspect
import warnings
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import EnumMeta
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ForwardRef,
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
from magicgui.widgets import _protocols

if TYPE_CHECKING:
    import numpy as np

    from ._concrete import Container


def create_widget(
    value: Any = None,
    annotation: Any = None,
    name: str = "",
    param_kind: Union[str, inspect._ParameterKind] = "POSITIONAL_OR_KEYWORD",
    label=None,
    gui_only=False,
    app=None,
    widget_type: Union[str, Type[_protocols.WidgetProtocol], None] = None,
    options: WidgetOptions = dict(),
):
    """Create and return appropriate widget subclass.

    This factory function can be used to create a widget appropriate for the
    provided ``value`` and/or ``annotation`` provided.

    Parameters
    ----------
    value : Any, optional
        The starting value for the widget, by default ``None``
    annotation : Any, optional
        The type annotation for the parameter represented by the widget, by default
        ``None``
    name : str, optional
        The name of the parameter represented by this widget. by default ``""``
    param_kind : str, optional
        The :attr:`inspect.Parameter.kind` represented by this widget.  Used in building
        signatures from multiple widgets, by default "``POSITIONAL_OR_KEYWORD``"
    label : str
        A string to use for an associated Label widget (if this widget is being
        shown in a :class:`~magicgui.widgets.Container` widget, and labels are on).
        By default, ``name`` will be used. Note: ``name`` refers the name of the
        parameter, as might be used in a signature, whereas label is just the label
        for that widget in the GUI.
    gui_only : bool, optional
        Whether the widget should be considered "only for the gui", or if it should
        be included in any widget container signatures, by default False
    app : str, optional
        The backend to use, by default ``None``
    widget_type : str or Type[WidgetProtocol] or None
        A class implementing a widget protocol or a string with the name of a
        magicgui widget type (e.g. "Label", "PushButton", etc...).
        If provided, this widget type will be used instead of the type
        autodetermined from ``value`` and/or ``annotation`` above.
    options : WidgetOptions, optional
        Dict of options to pass to the Widget constructor, by default dict()

    Returns
    -------
    Widget
        An instantiated widget subclass

    Raises
    ------
    TypeError
        If the provided or autodetected ``widget_type`` does not implement any known
        widget protocols from widgets._protocols.
    """
    kwargs = locals()
    _kind = kwargs.pop("param_kind", None)
    _app = use_app(kwargs.pop("app"))
    assert _app.native
    if isinstance(widget_type, _protocols.WidgetProtocol):
        wdg_class = kwargs.pop("widget_type")
    else:
        from magicgui.type_map import get_widget_class

        if widget_type:
            options["widget_type"] = widget_type
        wdg_class, opts = get_widget_class(value, annotation, options)

        if issubclass(wdg_class, Widget):
            opts.update(kwargs.pop("options"))
            kwargs.update(opts)
            kwargs.pop("widget_type", None)
            widget = wdg_class(**kwargs)
            if _kind:
                widget.param_kind = _kind
            return widget

    # pick the appropriate subclass for the given protocol
    # order matters
    for p in ("Categorical", "Ranged", "Button", "Value", ""):
        prot = getattr(_protocols, f"{p}WidgetProtocol")
        if isinstance(wdg_class, prot):
            options = kwargs.pop("options", {})
            widget = globals()[f"{p}Widget"](widget_type=wdg_class, **kwargs, **options)
            if _kind:
                widget.param_kind = _kind
            return widget

    raise TypeError(f"{wdg_class!r} does not implement any known widget protocols")


class Widget:
    """Basic Widget, wrapping a class that implements WidgetProtocol.

    Parameters
    ----------
    widget_type : Type[WidgetProtocol]
        A class implementing a widget protocol.  Will be instantiated during __init__.
    name : str, optional
        The name of the parameter represented by this widget. by default ""
    annotation : Any, optional
        The type annotation for the parameter represented by the widget, by default
        ``None``
    label : str
        A string to use for an associated Label widget (if this widget is being
        shown in a :class:`~magicgui.widgets.Container` widget, and labels are on).
        By default, ``name`` will be used. Note: ``name`` refers the name of the
        parameter, as might be used in a signature, whereas label is just the label
        for that widget in the GUI.
        Whether the widget should be considered "only for the gui", or if it should be
        included in any widget container signatures, by default False
    backend_kwargs : dict, optional
        keyword argument to pass to the backend widget constructor.
    """

    _widget: _protocols.WidgetProtocol

    def __init__(
        self,
        widget_type: Type[_protocols.WidgetProtocol],
        name: str = "",
        annotation: Any = None,
        label=None,
        visible: bool = True,
        gui_only=False,
        backend_kwargs=dict(),
        **extra,
    ):
        # for ipywidgets API compatibility
        label = label or extra.pop("description", None)
        if extra:
            warnings.warn(
                f"\n\n{self.__class__.__name__}.__init__() got unexpected "
                f"keyword arguments {set(extra)!r}.\n"
                "In the future this will raise an exception\n",
                FutureWarning,
            )

        _prot = self.__class__.__annotations__["_widget"]
        if not isinstance(_prot, str):
            _prot = _prot.__name__
        prot = getattr(_protocols, _prot.replace("_protocols.", ""))
        _protocols.assert_protocol(widget_type, prot)
        self.__magicgui_app__ = use_app()
        assert self.__magicgui_app__.native
        self._widget = widget_type(**backend_kwargs)
        self.name: str = name
        self.param_kind = inspect.Parameter.POSITIONAL_OR_KEYWORD
        self._label = label
        self.annotation: Any = annotation
        self.gui_only = gui_only
        self.visible: bool = True
        self.parent_changed = EventEmitter(source=self, type="parent_changed")
        self.label_changed = EventEmitter(source=self, type="label_changed")
        self._widget._mgui_bind_parent_change_callback(self._emit_parent)

        # put the magicgui widget on the native object...may cause error on some backend
        self.native._magic_widget = self
        self._post_init()
        if not visible:
            self.hide()

    def _emit_parent(self, event=None):
        self.parent_changed(value=self.parent)

    @property
    def annotation(self):
        """Return type annotation for the parameter represented by the widget.

        ForwardRefs will be resolve when setting the annotation.
        """
        return self._annotation

    @annotation.setter
    def annotation(self, value):
        if isinstance(value, (str, ForwardRef)):
            from magicgui.type_map import _evaluate_forwardref

            value = _evaluate_forwardref(value)
        self._annotation = value

    @property
    def param_kind(self) -> inspect._ParameterKind:
        """Return :attr:`inspect.Parameter.kind` represented by this widget.

        Used in building signatures from multiple widgets, by default
        :attr:`~inspect.Parameter.POSITIONAL_OR_KEYWORD`
        """
        return self._param_kind

    @param_kind.setter
    def param_kind(self, kind: Union[str, inspect._ParameterKind]):
        if isinstance(kind, str):
            kind = inspect._ParameterKind[kind.upper()]
        if not isinstance(kind, inspect._ParameterKind):
            raise TypeError(
                "'param_kind' must be either a string or a inspect._ParameterKind."
            )
        self._param_kind: inspect._ParameterKind = kind

    def _post_init(self):
        pass

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        # return {"enabled": self.enabled, "visible": self.visible}
        return {"visible": self.visible}

    @property
    def native(self):
        """Return native backend widget."""
        return self._widget._mgui_get_native_widget()

    def show(self, run=False):
        """Show the widget."""
        self._widget._mgui_show_widget()
        self.visible = True
        if run:
            self.__magicgui_app__.run()
        return self  # useful for generating repr in sphinx

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
        self._widget._mgui_hide_widget()
        self.visible = False

    @property
    def enabled(self) -> bool:
        """Whether widget is enabled (editable)."""
        return self._widget._mgui_get_enabled()

    @enabled.setter
    def enabled(self, value: bool):
        self._widget._mgui_set_enabled(value)

    @property
    def parent(self) -> Widget:
        """Return the parent widget."""
        return self._widget._mgui_get_parent()

    @parent.setter
    def parent(self, value: Widget):
        self._widget._mgui_set_parent(value)

    @property
    def widget_type(self) -> str:
        """Return type of widget."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        return f"{self.widget_type}(annotation={self.annotation!r}, name={self.name!r})"

    @property
    def label(self):
        """Return a label to use for this widget when present in Containers."""
        if self._label is None:
            return self.name.replace("_", " ")
        return self._label

    @label.setter
    def label(self, value):
        self._label = value
        self.label_changed(value=value)

    def render(self) -> "np.ndarray":
        """Return an RGBA (MxNx4) numpy array bitmap of the rendered widget."""
        return self._widget._mgui_render()

    def _repr_png_(self):
        """Return PNG representation of the widget for QtConsole."""
        from io import BytesIO

        try:
            from imageio import imsave
        except ImportError:
            print(
                "(For a nicer magicgui widget representation in "
                "Jupyter, please `pip install imageio`)"
            )
            return None

        with BytesIO() as file_obj:
            imsave(file_obj, self.render(), format="png")
            file_obj.seek(0)
            return file_obj.read()

    @property
    def width(self) -> int:
        """Return the current width of the widget.

        The naming of this method may change. The intention is to get the width of the
        widget after it is shown, for the purpose of unifying widget width in a layout.
        Backends may do what they need to accomplish this. For example, Qt can use
        ``sizeHint().width()``, since ``width()`` will return something large if the
        widget has not yet been painted on screen.
        """
        return self._widget._mgui_get_width()

    @width.setter
    def width(self, value: int) -> None:
        """Set the minimum allowable width of the widget."""
        self._widget._mgui_set_min_width(value)


class ValueWidget(Widget):
    """Widget with a value, Wraps ValueWidgetProtocol.

    Parameters
    ----------
    value : Any, optional
        The starting value for the widget, by default ``None``
    """

    _widget: _protocols.ValueWidgetProtocol
    changed: EventEmitter

    def __init__(self, value: Any = None, **kwargs):
        super().__init__(**kwargs)
        if value is not None:
            self.value = value

    def _post_init(self):
        super()._post_init()
        self.changed = EventEmitter(source=self, type="changed")
        self._widget._mgui_bind_change_callback(
            lambda *x: self.changed(value=x[0] if x else None)
        )

    @property
    def value(self):
        """Return current value of the widget.  This may be interpreted by backends."""
        return self._widget._mgui_get_value()

    @value.setter
    def value(self, value):
        return self._widget._mgui_set_value(value)

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        if hasattr(self, "_widget"):
            return (
                f"{self.widget_type}(value={self.value!r}, "
                f"annotation={self.annotation!r}, name={self.name!r})"
            )
        else:
            return f"<Uninitialized {self.widget_type}>"


class ButtonWidget(ValueWidget):
    """Widget with a value, Wraps ButtonWidgetProtocol.

    Parameters
    ----------
    text : str, optional
        The text to display on the button. If not provided, will use ``name``.
    """

    _widget: _protocols.ButtonWidgetProtocol
    changed: EventEmitter

    def __init__(self, text: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.text = text or self.name

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        d = super().options.copy()
        d.update({"text": self.text})
        return d

    @property
    def text(self):
        """Text of the widget."""
        return self._widget._mgui_get_text()

    @text.setter
    def text(self, value):
        self._widget._mgui_set_text(value)


class RangedWidget(ValueWidget):
    """Widget with a contstrained value. Wraps RangedWidgetProtocol.

    Parameters
    ----------
    min : float, optional
        The minimum allowable value, by default 0
    max : float, optional
        The maximum allowable value, by default 100
    step : float, optional
        The step size for incrementing the value, by default 1
    """

    _widget: _protocols.RangedWidgetProtocol

    def __init__(self, min: float = 0, max: float = 100, step: float = 1, **kwargs):
        for key in ("maximum", "minimum"):
            if key in kwargs:
                warnings.warn(
                    f"The {key!r} keyword arguments has been changed to {key[:3]!r}. "
                    "In the future this will raise an exception\n",
                    FutureWarning,
                )
                if key == "maximum":
                    max = kwargs.pop(key)
                else:
                    min = kwargs.pop(key)

        super().__init__(**kwargs)

        self.min = min
        self.max = max
        self.step = step

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        d = super().options.copy()
        d.update({"min": self.min, "max": self.max, "step": self.step})
        return d

    @property
    def min(self) -> float:
        """Minimum allowable value for the widget."""
        return self._widget._mgui_get_min()

    @min.setter
    def min(self, value: float):
        self._widget._mgui_set_min(value)

    @property
    def max(self) -> float:
        """Maximum allowable value for the widget."""
        return self._widget._mgui_get_max()

    @max.setter
    def max(self, value: float):
        self._widget._mgui_set_max(value)

    @property
    def step(self) -> float:
        """Step size for widget values."""
        return self._widget._mgui_get_step()

    @step.setter
    def step(self, value: float):
        self._widget._mgui_set_step(value)

    @property
    def range(self) -> Tuple[float, float]:
        """Range of allowable values for the widget."""
        return self.min, self.max

    @range.setter
    def range(self, value: Tuple[float, float]):
        self.min, self.max = value


class TransformedRangedWidget(RangedWidget, ABC):
    """Widget with a contstrained value. Wraps RangedWidgetProtocol.

    This can be used to map one domain of numbers onto another, useful for creating
    things like LogSliders.  Subclasses must reimplement ``_value_from_position`` and
    ``_position_from_value``.

    Parameters
    ----------
    min : float, optional
        The minimum allowable value, by default 0
    max : float, optional
        The maximum allowable value, by default 100
    min_pos : float, optional
        The minimum value for the *internal* (widget) position, by default 0.
    max_pos : float, optional
        The maximum value for the *internal* (widget) position, by default 0.
    step : float, optional
        The step size for incrementing the value, by default 1
    """

    _widget: _protocols.RangedWidgetProtocol

    def __init__(
        self,
        min: float = 0,
        max: float = 100,
        min_pos: int = 0,
        max_pos: int = 100,
        step: int = 1,
        **kwargs,
    ):
        self._min = min
        self._max = max
        self._min_pos = min_pos
        self._max_pos = max_pos
        ValueWidget.__init__(self, **kwargs)

        self._widget._mgui_set_min(self._min_pos)
        self._widget._mgui_set_max(self._max_pos)
        self._widget._mgui_set_step(step)

    # Just a linear scaling example.
    # Replace _value_from_position, and _position_from_value in subclasses
    # to implement more complex value->position lookups
    @property
    def _scale(self):
        """Slope of a linear map.  Just used as an example."""
        return (self.max - self.min) / (self._max_pos - self._min_pos)

    @abstractmethod
    def _value_from_position(self, position):
        """Return 'real' value given internal widget position."""
        return self.min + self._scale * (position - self._min_pos)

    @abstractmethod
    def _position_from_value(self, value):
        """Return internal widget position given 'real' value."""
        return (value - self.min) / self._scale + self._min_pos

    #########

    @property
    def value(self):
        """Return current value of the widget."""
        return self._value_from_position(self._widget._mgui_get_value())

    @value.setter
    def value(self, value):
        return self._widget._mgui_set_value(self._position_from_value(value))

    @property
    def min(self) -> float:
        """Minimum allowable value for the widget."""
        return self._min

    @min.setter
    def min(self, value: float):
        prev = self.value
        self._min = value
        self.value = prev

    @property
    def max(self) -> float:
        """Maximum allowable value for the widget."""
        return self._max

    @max.setter
    def max(self, value: float):
        prev = self.value
        self._max = value
        self.value = prev


class _OrientationMixin:
    """Properties for classes wrapping widgets that support orientation."""

    _widget: _protocols.SupportsOrientation

    @property
    def orientation(self) -> str:
        """Orientation of the widget."""
        return self._widget._mgui_get_orientation()

    @orientation.setter
    def orientation(self, value: str) -> None:
        if value not in {"horizontal", "vertical"}:
            raise ValueError(
                "Only horizontal and vertical orientation are currently supported"
            )
        self._widget._mgui_set_orientation(value)


class SliderWidget(RangedWidget, _OrientationMixin):
    """Widget with a contstrained value and orientation. Wraps SliderWidgetProtocol.

    Parameters
    ----------
    orientation : str, {'horizontal', 'vertical'}
        The orientation for the slider, by default "horizontal"
    """

    _widget: _protocols.SliderWidgetProtocol

    def __init__(self, orientation: str = "horizontal", **kwargs):
        super().__init__(**kwargs)

        self.orientation = orientation

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
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

    _widget: _protocols.CategoricalWidgetProtocol

    def __init__(self, choices: ChoicesType = (), **kwargs):
        self._default_choices = choices
        super().__init__(**kwargs)

    def _post_init(self):
        super()._post_init()
        self.reset_choices()
        self.parent_changed.connect(self.reset_choices)

    @property
    def value(self):
        """Return current value of the widget."""
        return self._widget._mgui_get_value()

    @value.setter
    def value(self, value):
        if value not in self.choices:
            raise ValueError(
                f"{value!r} is not a valid choice. must be in {self.choices}"
            )
        return self._widget._mgui_set_value(value)

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
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
    def current_choice(self) -> str:
        """Return the text of the currently selected choice."""
        return self._widget._mgui_get_current_choice()

    def __len__(self) -> int:
        """Return the number of choices."""
        return self._widget._mgui_get_count()

    def get_choice(self, choice_name: str):
        """Get data for the provided ``choice_name``."""
        self._widget._mgui_get_choice(choice_name)

    def set_choice(self, choice_name: str, data: Any = None):
        """Set data for the provided ``choice_name``."""
        data = data if data is not None else choice_name
        self._widget._mgui_set_choice(choice_name, data)
        if choice_name == self.current_choice:
            self.changed(value=self.value)

    def del_choice(self, choice_name: str, data: Any = None):
        """Delete the provided ``choice_name`` and associated data."""
        data = data if data is not None else choice_name

    @property
    def choices(self):
        """Available value choices for this widget."""
        return tuple(i[1] for i in self._widget._mgui_get_choices())

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

                n_params = len(inspect.signature(choices).parameters)
                if n_params > 1:
                    warnings.warn(
                        "\n\nAs of magicgui 0.2.0, when providing a callable to "
                        "`choices`, the\ncallable may accept only a single positional "
                        "argument (which will\nbe an instance of "
                        "`magicgui.widgets._bases.CategoricalWidget`),\nand must "
                        "return an iterable (the choices to show).\nFunction "
                        f"'{choices.__module__}.{choices.__name__}' accepts {n_params} "
                        "arguments.\nIn the future, this will raise an exception.\n",
                        FutureWarning,
                    )
                    # pre 0.2.0 API
                    _choices = choices(self.native, self.annotation)  # type: ignore
                else:
                    raise
        else:
            _choices = choices
        if not all(isinstance(i, tuple) and len(i) == 2 for i in _choices):
            _choices = [(str_func(i), i) for i in _choices]
        return self._widget._mgui_set_choices(_choices)


class ContainerWidget(Widget, _OrientationMixin, MutableSequence[Widget]):
    """Widget that can contain other widgets.

    Wraps a widget that implements
    :class:`~magicgui.widgets._protocols.ContainerProtocol`.

    A ``ContainerWidget`` behaves like a python list of :class:`Widget` objects.
    Subwidgets can be accessed using integer or slice-based indexing (``container[0]``),
    as well as by widget name (``container.<widget_name>``). Widgets can be
    added with ``append`` or ``insert``, and removed with ``del`` or ``pop``, etc...

    There is a tight connection between a ``ContainerWidget`` and an
    :class:`inspect.Signature` object, just as there is a tight connection between
    individual :class:`Widget` objects an an :class:`inspect.Parameter` object.
    The signature representation of a ``ContainerWidget`` (with the current settings
    as default values) is accessible with the :meth:`~ContainerWidget.to_signature`
    method (or by using :func:`inspect.signature` from the standard library)

    For a ``ContainerWidget`` sublcass that is tightly coupled to a specific function
    signature (as in the "classic" magicgui decorator), see
    :class:`~magicgui.function_gui.FunctionGui`.

    Parameters
    ----------
    layout : str, optional
        The layout for the container.  must be one of ``{'horizontal',
        'vertical'}``. by default "horizontal"
    widgets : Sequence[Widget], optional
        A sequence of widgets with which to intialize the container, by default
        ``None``.
    labels : bool, optional
        Whether each widget should be shown with a corresponding Label widget to the
        left, by default ``True``.  Note: the text for each widget defaults to
        ``widget.name``, but can be overriden by setting ``widget.label``.
    return_annotation : type or str, optional
        An optional return annotation to use when representing this container of
        widgets as an :class:`inspect.Signature`, by default ``None``
    """

    changed: EventEmitter
    _widget: _protocols.ContainerProtocol
    _initialized = False

    def __init__(
        self,
        layout: str = "horizontal",
        widgets: Sequence[Widget] = (),
        labels=True,
        return_annotation: Any = None,
        **kwargs,
    ):
        self._return_annotation = None
        self._labels = labels
        self._layout = layout
        kwargs["backend_kwargs"] = {"layout": layout}
        super().__init__(**kwargs)
        self.changed = EventEmitter(source=self, type="changed")
        self.return_annotation = return_annotation
        self.extend(widgets)
        self.parent_changed.connect(self.reset_choices)
        self._initialized = True
        self._unify_label_widths()

    @property
    def return_annotation(self):
        """Return annotation to use when converting to :class:`inspect.Signature`.

        ForwardRefs will be resolve when setting the annotation.
        """
        return self._return_annotation

    @return_annotation.setter
    def return_annotation(self, value):
        if isinstance(value, (str, ForwardRef)):
            from magicgui.type_map import _evaluate_forwardref

            value = _evaluate_forwardref(value)
        self._return_annotation = value

    def __getattr__(self, name: str):
        """Return attribute ``name``.  Will return a widget if present."""
        for widget in self:
            if name == widget.name:
                return widget
        return object.__getattribute__(self, name)

    def __setattr__(self, name: str, value: Any):
        """Set attribute ``name``.  Prevents changing widget if present, (use del)."""
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
    def __getitem__(self, key: Union[int, str]) -> Widget:  # noqa: D105
        ...

    @overload
    def __getitem__(self, key: slice) -> MutableSequence[Widget]:  # noqa: F811, D105
        ...

    def __getitem__(self, key):  # noqa: F811
        """Get item by integer, str, or slice."""
        if isinstance(key, str):
            return self.__getattr__(key)
        if isinstance(key, slice):
            out = []
            for idx in range(*key.indices(len(self))):
                item = self._widget._mgui_get_index(idx)
                if item:
                    out.append(item)
            return out
        elif isinstance(key, int):
            if key < 0:
                key += len(self)
        item = self._widget._mgui_get_index(key)
        if not item:
            raise IndexError("Container index out of range")
        return getattr(item, "_inner_widget", item)

    def index(self, value: Any, start=0, stop=9223372036854775807) -> int:
        """Return index of a specific widget instance (or widget name)."""
        if isinstance(value, str):
            value = getattr(self, value)
        return super().index(value, start, stop)

    def remove(self, value: Union[Widget, str]):
        """Remove a widget instance (may also be string name of widget)."""
        super().remove(value)  # type: ignore

    def __delattr__(self, name: str):
        """Delete a widget by name."""
        self.remove(name)

    def __delitem__(self, key: Union[int, slice]):
        """Delete a widget by integer or slice index."""
        if isinstance(key, slice):
            for idx in range(*key.indices(len(self))):
                self._widget._mgui_remove_index(idx)
        else:
            if key < 0:
                key += len(self)
            self._widget._mgui_remove_index(key)

    def __len__(self) -> int:
        """Return the count of widgets."""
        return self._widget._mgui_count()

    def __setitem__(self, key, value):
        """Prevent assignment by index."""
        raise NotImplementedError("magicgui.Container does not support item setting.")

    def __dir__(self) -> List[str]:
        """Add subwidget names to the dir() call for this widget."""
        d = list(super().__dir__())
        d.extend([w.name for w in self if not w.gui_only])
        return d

    def insert(self, key: int, widget: Widget):
        """Insert widget at ``key``."""
        if isinstance(widget, ValueWidget):
            widget.changed.connect(lambda x: self.changed(value=self))
        _widget = widget

        if self.labels:
            from ._concrete import _LabeledWidget

            # no labels for button widgets (push buttons, checkboxes, have their own)
            if not isinstance(widget, (_LabeledWidget, ButtonWidget)):
                _widget = _LabeledWidget(widget)
                widget.label_changed.connect(self._unify_label_widths)

        self._widget._mgui_insert_widget(key, _widget)
        self._unify_label_widths()

    def _unify_label_widths(self, event=None):
        if not self._initialized:
            return
        if self.layout == "vertical" and self.labels and len(self):
            measure = use_app().get_obj("get_text_width")
            widest_label = max(
                measure(w.label) for w in self if not isinstance(w, ButtonWidget)
            )
            for i in range(len(self)):
                w = self._widget._mgui_get_index(i)
                if hasattr(w, "label_width"):
                    w.label_width = widest_label  # type: ignore

    @property
    def margins(self) -> Tuple[int, int, int, int]:
        """Return margin between the content and edges of the container."""
        return self._widget._mgui_get_margins()

    @margins.setter
    def margins(self, margins: Tuple[int, int, int, int]) -> None:
        # left, top, right, bottom
        self._widget._mgui_set_margins(margins)

    @property
    def layout(self) -> str:
        """Return the layout of the widget."""
        return self._layout

    @layout.setter
    def layout(self, value):
        raise NotImplementedError(
            "It is not yet possible to change layout after instantiation"
        )

    @property
    def native_layout(self):
        """Return the layout widget used by the backend."""
        return self._widget._mgui_get_native_layout()

    def reset_choices(self, event=None):
        """Reset choices for all Categorical subWidgets to the default state.

        If widget._default_choices is a callable, this may NOT be the exact same set of
        choices as when the widget was instantiated, if the callable relies on external
        state.
        """
        for widget in self:
            if isinstance(widget, CategoricalWidget):
                widget.reset_choices()

    def refresh_choices(self, event=None):
        """Alias for reset_choices [DEPRECATED: use reset_choices]."""
        warnings.warn(
            "\n`ContainerWidget.refresh_choices` is deprecated and will be removed in a"
            " future version, please use `ContainerWidget.reset_choices` instead.",
            FutureWarning,
        )
        return self.reset_choices(event)

    @property
    def __signature__(self) -> inspect.Signature:
        """Return signature object, for compatibility with inspect.signature()."""
        return self.to_signature()

    def to_signature(self) -> MagicSignature:
        """Return a MagicSignature object representing the current state of the gui."""
        params = [
            MagicParameter.from_widget(w) for w in self if w.name and not w.gui_only
        ]
        return MagicSignature(params, return_annotation=self.return_annotation)

    @classmethod
    def from_signature(cls, sig: inspect.Signature, **kwargs) -> Container:
        """Create a Container widget from an inspect.Signature object."""
        return MagicSignature.from_signature(sig).to_container(**kwargs)

    @classmethod
    def from_callable(
        cls, obj: Callable, gui_options: Optional[dict] = None, **kwargs
    ) -> Container:
        """Create a Container widget from a callable object.

        In most cases, it will be preferable to create a ``FunctionGui`` instead.
        """
        return magic_signature(obj, gui_options=gui_options).to_container(**kwargs)

    def __repr__(self) -> str:
        """Return a repr."""
        return f"<Container {self.to_signature()}>"

    @property
    def labels(self) -> bool:
        """Whether widgets are presented with labels."""
        return self._labels

    @labels.setter
    def labels(self, value: bool):
        if value == self._labels:
            return
        self._labels = value

        for index, _ in enumerate(self):
            widget = self.pop(index)
            self.insert(index, widget)
