from __future__ import annotations

import contextlib
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterable,
    Mapping,
    MutableSequence,
    NoReturn,
    Sequence,
    TypeVar,
    overload,
)

from psygnal import Signal

from magicgui._util import debounce
from magicgui.application import use_app
from magicgui.signature import MagicParameter, MagicSignature, magic_signature
from magicgui.widgets.bases._mixins import _OrientationMixin

from ._button_widget import ButtonWidget
from ._value_widget import ValueWidget
from ._widget import Widget

WidgetVar = TypeVar("WidgetVar", bound=Widget)

if TYPE_CHECKING:
    import inspect
    from pathlib import Path

    from typing_extensions import Unpack

    from magicgui.widgets import Container, protocols

    from ._widget import WidgetKwargs

    class ContainerKwargs(WidgetKwargs, Generic[WidgetVar], total=False):
        widgets: Sequence[WidgetVar]
        layout: str
        scrollable: bool
        labels: bool


class ContainerWidget(Widget, _OrientationMixin, MutableSequence[WidgetVar]):
    """Widget that can contain other widgets.

    Wraps a widget that implements
    [`ContainerProtocol`][magicgui.widgets.protocols.ContainerProtocol].

    A `ContainerWidget` behaves like a python list of [Widget][magicgui.widgets.Widget]
    objects. Subwidgets can be accessed using integer or slice-based indexing
    (`container[0]`), as well as by widget name (`container.<widget_name>`). Widgets can
    be added with `append` or `insert`, and removed with `del` or `pop`, etc...

    There is a tight connection between a `ContainerWidget` and an
    [inspect.Signature][inspect.Signature] object,
    just as there is a tight connection between individual [Widget` objects an
    an :class:`inspect.Parameter][inspect.Parameter] object.
    The signature representation of a `ContainerWidget`
    (with the current settings as default values) is accessible with
    the :meth:`~ContainerWidget.__signature__` method (or by using
    :func:`inspect.signature` from the standard library)

    For a `ContainerWidget` subclass that is tightly coupled to a specific function
    signature (as in the "classic" magicgui decorator), see
    [magicgui.widgets.FunctionGui][magicgui.widgets.FunctionGui].

    Parameters
    ----------
    widgets : Sequence[Widget], optional
        A sequence of widgets with which to initialize the container, by default
        `None`.
    layout : str, optional
        The layout for the container.  must be one of `{'horizontal',
        'vertical'}`. by default "vertical"
    scrollable : bool, optional
        Whether to enable scroll bars or not. If enabled, scroll bars will
        only appear along the layout direction, not in both directions.
    labels : bool, optional
        Whether each widget should be shown with a corresponding Label widget to the
        left, by default `True`.  Note: the text for each widget defaults to
        `widget.name`, but can be overridden by setting `widget.label`.
    **base_widget_kwargs : Any
        All additional keyword arguments are passed to the base
        [`magicgui.widgets.Widget`][magicgui.widgets.Widget] constructor.
    """

    changed = Signal(
        object,
        description="Emitted with `self` when any sub-widget in the container changes.",
    )
    _widget: protocols.ContainerProtocol
    _initialized = False
    # this is janky ... it's here to allow connections during __init__ by
    # avoiding a recursion error in __getattr__
    _list: list[WidgetVar] = []  # noqa: RUF012

    def __init__(
        self,
        widgets: Sequence[WidgetVar] = (),
        *,
        layout: str = "vertical",
        scrollable: bool = False,
        labels: bool = True,
        **base_widget_kwargs: Unpack[WidgetKwargs],
    ) -> None:
        self._list: list[WidgetVar] = []
        self._labels = labels
        self._layout = layout
        self._scrollable = scrollable
        base_widget_kwargs.setdefault("backend_kwargs", {}).update(  # type: ignore
            {"layout": layout, "scrollable": scrollable}
        )
        super().__init__(**base_widget_kwargs)
        self.extend(widgets)
        self.native_parent_changed.connect(self.reset_choices)
        self._initialized = True
        self._unify_label_widths()

    def __getattr__(self, name: str) -> WidgetVar:
        """Return attribute ``name``.  Will return a widget if present."""
        for widget in self._list:
            if name == widget.name:
                return widget
        return object.__getattribute__(self, name)  # type: ignore

    def __setattr__(self, name: str, value: Any) -> None:
        """Set attribute ``name``.  Prevents changing widget if present, (use del)."""
        if self._initialized:
            for widget in self._list:
                if name == widget.name:
                    raise AttributeError(
                        "Cannot set attribute with same name as a widget\n"
                        "If you are trying to change the value of a widget, use: "
                        f"`{self.__class__.__name__}.{name}.value = {value}`",
                    )
        object.__setattr__(self, name, value)

    @overload
    def __getitem__(self, key: int | str) -> WidgetVar: ...

    @overload
    def __getitem__(self, key: slice) -> MutableSequence[WidgetVar]: ...

    def __getitem__(
        self, key: int | str | slice
    ) -> WidgetVar | MutableSequence[WidgetVar]:
        """Get item by integer, str, or slice."""
        if isinstance(key, str):
            return self.__getattr__(key)
        if isinstance(key, slice):
            return [getattr(item, "_inner_widget", item) for item in self._list[key]]
        elif isinstance(key, int):
            item = self._list[key]
            return getattr(item, "_inner_widget", item)
        raise TypeError(f"list indices must be integers or slices, not {type(key)}")

    def index(self, value: Any, start: int = 0, stop: int = 9223372036854775807) -> int:
        """Return index of a specific widget instance (or widget name)."""
        if isinstance(value, str):
            value = getattr(self, value)
        return super().index(value, start, stop)

    def remove(self, value: Widget | str) -> None:
        """Remove a widget instance (may also be string name of widget)."""
        super().remove(value)  # type: ignore

    def __delattr__(self, name: str) -> None:
        """Delete a widget by name."""
        self.remove(name)

    def __delitem__(self, key: int | slice) -> None:
        """Delete a widget by integer or slice index."""
        if isinstance(key, slice):
            for item in self._list[key]:
                ref = getattr(item, "_labeled_widget_ref", None)
                if ref:
                    item = ref()
                self._widget._mgui_remove_widget(item)
        elif isinstance(key, int):
            item = self._list[key]
            ref = getattr(item, "_labeled_widget_ref", None)
            if ref:
                item = item._labeled_widget_ref()  # type: ignore
            self._widget._mgui_remove_widget(item)
        else:
            raise TypeError(f"list indices must be integers or slices, not {type(key)}")
        del self._list[key]

    def __len__(self) -> int:
        """Return the count of widgets."""
        return len(self._list)

    def __setitem__(self, key: Any, value: Any) -> NoReturn:
        """Prevent assignment by index."""
        raise RuntimeError("magicgui.Container does not support item setting.")

    def __dir__(self) -> list[str]:
        """Add subwidget names to the dir() call for this widget."""
        d = list(super().__dir__())
        d.extend([w.name for w in self._list if not w.gui_only])
        return d

    def insert(self, key: int, widget: WidgetVar) -> None:
        """Insert widget at ``key``."""
        if isinstance(widget, (ValueWidget, ContainerWidget)):
            widget.changed.connect(lambda: self.changed.emit(self))
        _widget = widget

        if self.labels:
            from magicgui.widgets._concrete import _LabeledWidget

            # no labels for button widgets (push buttons, checkboxes, have their own)
            if not isinstance(widget, (_LabeledWidget, ButtonWidget)):
                _widget = _LabeledWidget(widget)  # type: ignore
                widget.label_changed.connect(self._unify_label_widths)

        if key < 0:
            key += len(self)
        self._list.insert(key, widget)
        # NOTE: if someone has manually mucked around with self.native.layout()
        # it's possible that indices will be off.
        self._widget._mgui_insert_widget(key, _widget)
        self._unify_label_widths()

    def _unify_label_widths(self) -> None:
        if not self._initialized:
            return

        need_labels = [w for w in self._list if not isinstance(w, ButtonWidget)]
        if self.layout == "vertical" and self.labels and need_labels:
            measure = use_app().get_obj("get_text_width")
            widest_label = max(measure(w.label) for w in need_labels)
            for w in self:
                labeled_widget = w._labeled_widget()
                if labeled_widget:
                    labeled_widget.label_width = widest_label

    @property
    def margins(self) -> tuple[int, int, int, int]:
        """Return margin between the content and edges of the container."""
        return self._widget._mgui_get_margins()

    @margins.setter
    def margins(self, margins: tuple[int, int, int, int]) -> None:
        # left, top, right, bottom
        self._widget._mgui_set_margins(margins)

    @property
    def layout(self) -> str:
        """Return the layout of the widget."""
        return self._layout

    @layout.setter
    def layout(self, value: str) -> NoReturn:
        raise NotImplementedError(
            "It is not yet possible to change layout after instantiation"
        )

    def reset_choices(self, *_: Any) -> None:
        """Reset choices for all Categorical subWidgets to the default state.

        If widget._default_choices is a callable, this may NOT be the exact same set of
        choices as when the widget was instantiated, if the callable relies on external
        state.
        """
        for widget in self._list:
            if hasattr(widget, "reset_choices"):
                widget.reset_choices()

    @property
    def __signature__(self) -> MagicSignature:
        """Return a MagicSignature object representing the current state of the gui."""
        params = [
            MagicParameter.from_widget(w)
            for w in self._list
            if w.name and not w.gui_only
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
        return MagicSignature(params)

    @classmethod
    def from_signature(
        cls, sig: inspect.Signature, **kwargs: Unpack[ContainerKwargs]
    ) -> Container:
        """Create a Container widget from an inspect.Signature object."""
        return MagicSignature.from_signature(sig).to_container(**kwargs)

    @classmethod
    def from_callable(
        cls,
        obj: Callable,
        gui_options: dict | None = None,
        **kwargs: Unpack[ContainerKwargs],
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
    def labels(self, value: bool) -> None:
        if value == self._labels:
            return
        self._labels = value

        for index, _ in enumerate(self):
            widget = self.pop(index)
            self.insert(index, widget)

    NO_VALUE = "NO_VALUE"

    def asdict(self) -> dict[str, Any]:
        """Return state of widget as dict."""
        return {
            w.name: getattr(w, "value", None)
            for w in self._list
            if w.name and not w.gui_only
        }

    def update(
        self,
        mapping: Mapping | Iterable[tuple[str, Any]] | None = None,
        **kwargs: Any,
    ) -> None:
        """Update the parameters in the widget from a mapping, iterable, or kwargs."""
        with self.changed.blocked():
            if mapping:
                items = mapping.items() if isinstance(mapping, Mapping) else mapping
                for key, value in items:
                    getattr(self, key).value = value
            for key, value in kwargs.items():
                getattr(self, key).value = value
        self.changed.emit()

    @debounce
    def _dump(self, path: str | Path) -> None:
        """Dump the state of the widget to `path`."""
        import pickle
        from pathlib import Path

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        _dict = {}
        for widget in self._list:
            try:
                # not all values will be pickleable and restorable...
                # for now, don't even try
                _v = pickle.dumps(getattr(widget, "value", self.NO_VALUE))
                _dict[widget.name] = _v
            except Exception:
                continue

        path.write_bytes(pickle.dumps(_dict))

    def _load(self, path: str | Path, quiet: bool = False) -> None:
        """Restore the state of the widget from previously saved file at `path`."""
        import pickle
        from pathlib import Path

        path = Path(path)
        if not path.exists():
            if quiet:
                return
            raise FileNotFoundError(f"Widget state file does not exist: {path}")

        try:
            data: dict = pickle.loads(path.read_bytes())
        except Exception:
            if quiet:
                path.unlink(missing_ok=True)
                return
            raise

        for key, val in data.items():
            with contextlib.suppress(ValueError, AttributeError):
                val = pickle.loads(val)
                if val != self.NO_VALUE:
                    getattr(self, key).value = val


class MainWindowWidget(ContainerWidget):
    """Top level Application widget that can contain other widgets."""

    _widget: protocols.MainWindowProtocol

    def create_menu_item(
        self,
        menu_name: str,
        item_name: str,
        callback: Callable | None = None,
        shortcut: str | None = None,
    ) -> None:
        """Create a menu item ``item_name`` under menu ``menu_name``.

        ``menu_name`` will be created if it does not already exist.
        """
        self._widget._mgui_create_menu_item(menu_name, item_name, callback, shortcut)


class DialogWidget(ContainerWidget):
    """Modal Container."""

    _widget: protocols.DialogProtocol

    def exec(self) -> bool:
        """Show the dialog, and block.

        Return True if the dialog was accepted, False if rejected.
        """
        return bool(self._widget._mgui_exec())
