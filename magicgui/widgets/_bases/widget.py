from __future__ import annotations

import inspect
import sys
import warnings
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional

from psygnal import Signal

from magicgui._type_wrapper import resolve_forward_refs
from magicgui.application import use_app
from magicgui.widgets import _protocols

BUILDING_DOCS = sys.argv[-2:] == ["build", "docs"]
if BUILDING_DOCS:
    import numpy as np

if TYPE_CHECKING:
    from weakref import ReferenceType

    import numpy as np  # noqa

    from magicgui.widgets._concrete import _LabeledWidget


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
    tooltip : str, optional
        A tooltip to display when hovering over the widget.
    visible : bool, optional
        Whether the widget is visible, by default ``True``.
    enabled : bool, optional
        Whether the widget is enabled, by default ``True``.
    gui_only : bool, optional
        If ``True``, widget is excluded from any function signature representation.
        by default ``False``.  (This will likely be deprecated.)
    parent : Widget, optional
        Optional parent widget of this widget.  CAREFUL: if a parent is set, and
        subsequently deleted, this widget will likely be deleted as well (depending on
        the backend), and will no longer be usable.
    backend_kwargs : dict, optional
        keyword argument to pass to the backend widget constructor.
    """

    _widget: _protocols.WidgetProtocol
    # if this widget becomes owned by a labeled widget
    _labeled_widget_ref: ReferenceType[_LabeledWidget] | None = None

    parent_changed = Signal(object)
    label_changed = Signal(str)

    def __init__(
        self,
        widget_type: type[_protocols.WidgetProtocol],
        name: str = "",
        annotation: Any = None,
        label: str = None,
        tooltip: str | None = None,
        visible: bool | None = None,
        enabled: bool = True,
        gui_only: bool = False,
        parent: Any = None,
        backend_kwargs=dict(),
        **extra,
    ):
        # for ipywidgets API compatibility
        label = label or extra.pop("description", None)
        if extra:
            raise TypeError(
                f"{type(self).__name__} got an unexpected "
                f"keyword argument: {', '.join(extra)}"
            )
        for m in self.__class__.__mro__[:-1]:
            _prot = m.__annotations__.get("_widget")
            if _prot:
                break
        else:
            raise TypeError(
                f"Widget type {self.__class__} declared no _widget annotation"
            )
        if not isinstance(_prot, str):
            _prot = _prot.__name__
        prot = getattr(_protocols, _prot.replace("_protocols.", ""))
        _protocols.assert_protocol(widget_type, prot)
        self.__magicgui_app__ = use_app()
        assert self.__magicgui_app__.native
        if isinstance(parent, Widget):
            parent = parent.native
        try:
            self._widget = widget_type(parent=parent, **backend_kwargs)
        except TypeError as e:
            if "unexpected keyword" not in str(e) and "no arguments" not in str(e):
                raise

            warnings.warn(
                "Beginning with magicgui v0.6, the `widget_type` class passed to "
                "`magicgui.Widget` must accept a `parent` Argument. In v0.7 this "
                "will raise an exception. "
                f"Please update '{widget_type.__name__}.__init__()'",
                stacklevel=2,
            )
            self._widget = widget_type(**backend_kwargs)

        self.name: str = name
        self.param_kind = inspect.Parameter.POSITIONAL_OR_KEYWORD
        self._label = label
        self.tooltip = tooltip
        self.enabled = enabled
        self.annotation: Any = annotation
        self.gui_only = gui_only
        self._widget._mgui_bind_parent_change_callback(self._emit_parent)

        # put the magicgui widget on the native object...may cause error on some backend
        self.native._magic_widget = self
        self._post_init()
        self._visible: bool = False
        self._explicitly_hidden: bool = False
        if visible is not None:
            self.visible = visible

    @property
    def annotation(self):
        """Return type annotation for the parameter represented by the widget.

        ForwardRefs will be resolve when setting the annotation.
        """
        return self._annotation

    @annotation.setter
    def annotation(self, value):
        self._annotation = resolve_forward_refs(value)

    @property
    def param_kind(self) -> inspect._ParameterKind:
        """Return :attr:`inspect.Parameter.kind` represented by this widget.

        Used in building signatures from multiple widgets, by default
        :attr:`~inspect.Parameter.POSITIONAL_OR_KEYWORD`
        """
        return self._param_kind

    @param_kind.setter
    def param_kind(self, kind: str | inspect._ParameterKind):
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
        return {"enabled": self.enabled, "visible": self.visible}

    @property
    def native(self):
        """
        Return native backend widget.

        Note this is the widget that contains the layout, and not any
        parent widgets of this (e.g. a parent widget that is used to
        enable scroll bars)
        """
        return self._widget._mgui_get_native_widget()

    @property
    def root_native_widget(self):
        """
        Return the root native backend widget.

        This can be different from the ``.native`` widget if the layout
        is a child of some other widget, e.g. a widget used to enable
        scroll bars.
        """
        return self._widget._mgui_get_root_native_widget()

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

    @property
    def label(self):
        """Return a label to use for this widget when present in Containers."""
        if self._label is None:
            return self.name.replace("_", " ")
        return self._label

    @label.setter
    def label(self, value):
        self._label = value
        self.label_changed.emit(value)

    @property
    def width(self) -> int:
        """Return the current width of the widget."""
        return self._widget._mgui_get_width()

    @width.setter
    def width(self, value: int) -> None:
        """Set the minimum allowable width of the widget."""
        self._widget._mgui_set_width(value)

    @property
    def min_width(self) -> int:
        """Get the minimum width of the widget."""
        return self._widget._mgui_get_min_width()

    @min_width.setter
    def min_width(self, value: int) -> None:
        """Set the minimum width of the widget."""
        self._widget._mgui_set_min_width(value)

    @property
    def max_width(self) -> int:
        """Get the maximum width of the widget."""
        return self._widget._mgui_get_max_width()

    @max_width.setter
    def max_width(self, value: int) -> None:
        """Set the maximum width of the widget."""
        self._widget._mgui_set_max_width(value)

    @property
    def height(self) -> int:
        """Return the current height of the widget."""
        return self._widget._mgui_get_height()

    @height.setter
    def height(self, value: int) -> None:
        """Set the minimum allowable height of the widget."""
        self._widget._mgui_set_height(value)

    @property
    def min_height(self) -> int:
        """Get the minimum height of the widget."""
        return self._widget._mgui_get_min_height()

    @min_height.setter
    def min_height(self, value: int) -> None:
        """Set the minimum height of the widget."""
        self._widget._mgui_set_min_height(value)

    @property
    def max_height(self) -> int:
        """Get the maximum height of the widget."""
        return self._widget._mgui_get_max_height()

    @max_height.setter
    def max_height(self, value: int) -> None:
        """Set the maximum height of the widget."""
        self._widget._mgui_set_max_height(value)

    @property
    def tooltip(self) -> str | None:
        """Get the tooltip for this widget."""
        return self._widget._mgui_get_tooltip() or None

    @tooltip.setter
    def tooltip(self, value: str | None) -> None:
        """Set the tooltip for this widget."""
        return self._widget._mgui_set_tooltip(value)

    def _labeled_widget(self) -> _LabeledWidget | None:
        """Return _LabeledWidget container, if applicable."""
        return self._labeled_widget_ref() if self._labeled_widget_ref else None

    @property
    def visible(self) -> bool:
        """Return whether widget is visible."""
        return self._widget._mgui_get_visible()

    @visible.setter
    def visible(self, value: bool):
        """Set widget visibility.

        ``widget.show()`` is an alias for ``widget.visible = True``
        ``widget.hide()`` is an alias for ``widget.visible = False``
        """
        if value is None:
            return

        self._widget._mgui_set_visible(value)
        self._explicitly_hidden = not value

        labeled_widget = self._labeled_widget()
        if labeled_widget is not None:
            labeled_widget.visible = value

    def show(self, run=False):
        """Show widget.

        alias for ``widget.visible = True``

        Parameters
        ----------
        run : bool, optional
            Whether to start the application event loop, by default False
        """
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
        """Hide widget.

        alias for ``widget.visible = False``
        """
        self.visible = False

    def close(self) -> None:
        """Close widget."""
        self._widget._mgui_close_widget()

    def render(self) -> np.ndarray:
        """Return an RGBA (MxNx4) numpy array bitmap of the rendered widget."""
        return self._widget._mgui_render()

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        return f"{self.widget_type}(annotation={self.annotation!r}, name={self.name!r})"

    def _repr_png_(self) -> Optional[bytes]:
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

        rendered = self.render()
        if rendered is not None:
            with BytesIO() as file_obj:
                imsave(file_obj, rendered, format="png")
                file_obj.seek(0)
                return file_obj.read()
        return None

    def _emit_parent(self, *_):
        self.parent_changed.emit(self.parent)

    def _ipython_display_(self, *args, **kwargs):
        if hasattr(self.native, "_ipython_display_"):
            return self.native._ipython_display_(*args, **kwargs)
        raise NotImplementedError()

    def _repr_mimebundle_(self, *args, **kwargs):
        if hasattr(self.native, "_repr_mimebundle_"):
            return self.native._repr_mimebundle_(*args, **kwargs)
        raise NotImplementedError()
