from __future__ import annotations

import inspect
import warnings
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
    Union,
    overload,
)

from magicgui.application import use_app
from magicgui.events import EventEmitter
from magicgui.signature import MagicParameter, MagicSignature, magic_signature
from magicgui.widgets import _protocols
from magicgui.widgets._bases.mixins import _OrientationMixin

from .button_widget import ButtonWidget
from .value_widget import ValueWidget
from .widget import Widget

if TYPE_CHECKING:
    from magicgui.widgets import Container


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
    as default values) is accessible with the :meth:`~ContainerWidget.__signature__`
    method (or by using :func:`inspect.signature` from the standard library)

    For a ``ContainerWidget`` sublcass that is tightly coupled to a specific function
    signature (as in the "classic" magicgui decorator), see
    :class:`~magicgui.widgets.FunctionGui`.

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
        layout: str = "vertical",
        widgets: Sequence[Widget] = (),
        labels=True,
        return_annotation: Any = None,
        **kwargs,
    ):
        self._list: List[Widget] = []
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
            return [getattr(item, "_inner_widget", item) for item in self._list[key]]
        elif isinstance(key, int):
            item = self._list[key]
            return getattr(item, "_inner_widget", item)
        raise TypeError(f"list indices must be integers or slices, not {type(key)}")

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
            for item in self._list[key]:
                self._widget._mgui_remove_widget(item)
        elif isinstance(key, int):
            self._widget._mgui_remove_widget(self._list[key])
        else:
            raise TypeError(f"list indices must be integers or slices, not {type(key)}")
        del self._list[key]

    def __len__(self) -> int:
        """Return the count of widgets."""
        return len(self._list)

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
            from magicgui.widgets._concrete import _LabeledWidget

            # no labels for button widgets (push buttons, checkboxes, have their own)
            if not isinstance(widget, (_LabeledWidget, ButtonWidget)):
                _widget = _LabeledWidget(widget)
                widget.label_changed.connect(self._unify_label_widths)

        self._list.insert(key, widget)
        if key < 0:
            key += len(self)
        # NOTE: if someone has manually mucked around with self.native.layout()
        # it's possible that indices will be off.
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
            for w in self:
                labeled_widget = w._labeled_widget()
                if labeled_widget:
                    labeled_widget.label_width = widest_label

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

    def reset_choices(self, event=None):
        """Reset choices for all Categorical subWidgets to the default state.

        If widget._default_choices is a callable, this may NOT be the exact same set of
        choices as when the widget was instantiated, if the callable relies on external
        state.
        """
        for widget in self:
            if hasattr(widget, "reset_choices"):
                widget.reset_choices()  # type: ignore

    def refresh_choices(self, event=None):
        """Alias for reset_choices [DEPRECATED: use reset_choices]."""
        warnings.warn(
            "\n`ContainerWidget.refresh_choices` is deprecated and will be removed in a"
            " future version, please use `ContainerWidget.reset_choices` instead.",
            FutureWarning,
        )
        return self.reset_choices(event)

    @property
    def __signature__(self) -> MagicSignature:
        """Return a MagicSignature object representing the current state of the gui."""
        params = [
            MagicParameter.from_widget(w) for w in self if w.name and not w.gui_only
        ]
        # if we have multiple non-default parameters and some but not all of them are
        # "bound" to fallback values, we may have  non-default arguments
        # following default arguments
        seen_default = False
        for p in params:
            if p.default is not p.empty:
                seen_default = True
            elif seen_default:
                params.sort(key=lambda x: x.default is not MagicParameter.empty)
                break
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
        return f"<Container {self.__signature__}>"

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


class MainWindowWidget(ContainerWidget):
    """Top level Application widget that can contain other widgets."""

    _widget: _protocols.MainWindowProtocol

    def create_menu_item(
        self, menu_name: str, item_name: str, callback=None, shortcut=None
    ):
        """Create a menu item ``item_name`` under menu ``menu_name``.

        ``menu_name`` will be created if it does not already exist.
        """
        self._widget._mgui_create_menu_item(menu_name, item_name, callback, shortcut)
