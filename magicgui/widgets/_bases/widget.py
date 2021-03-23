from __future__ import annotations

import inspect
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, ForwardRef

from magicgui.application import use_app
from magicgui.events import EventEmitter
from magicgui.widgets import _protocols

if TYPE_CHECKING:
    from weakref import ReferenceType

    import numpy as np

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
    backend_kwargs : dict, optional
        keyword argument to pass to the backend widget constructor.
    """

    _widget: _protocols.WidgetProtocol
    # if this widget becomes owned by a labeled widget
    _labeled_widget_ref: ReferenceType[_LabeledWidget] | None = None

    def __init__(
        self,
        widget_type: type[_protocols.WidgetProtocol],
        name: str = "",
        annotation: Any = None,
        label: str = None,
        tooltip: str | None = None,
        visible: bool | None = None,
        enabled: bool = True,
        gui_only=False,
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
        self.tooltip = tooltip
        self.enabled = enabled
        self.annotation: Any = annotation
        self.gui_only = gui_only
        self.parent_changed = EventEmitter(source=self, type="parent_changed")
        self.label_changed = EventEmitter(source=self, type="label_changed")
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
        """Return native backend widget."""
        return self._widget._mgui_get_native_widget()

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
        self.label_changed(value=value)

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

    def render(self) -> np.ndarray:
        """Return an RGBA (MxNx4) numpy array bitmap of the rendered widget."""
        return self._widget._mgui_render()

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        return f"{self.widget_type}(annotation={self.annotation!r}, name={self.name!r})"

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

    def _emit_parent(self, event=None):
        self.parent_changed(value=self.parent)
