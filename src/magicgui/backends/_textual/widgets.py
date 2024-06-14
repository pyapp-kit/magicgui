from typing import TYPE_CHECKING, Any, Callable, cast

from textual import widgets as txtwdgs
from textual.widget import Widget as TxWidget

from magicgui.widgets import protocols

from .application import MguiApp

try:
    # useful, but not yet public...
    from psygnal._weak_callback import WeakCallback, weak_callback

except ImportError:
    WeakCallback = Callable[[Any], Any]

    def weak_callback(callback: Callable[[Any], Any]) -> WeakCallback:
        return callback


if TYPE_CHECKING:
    import numpy as np
    from textual.dom import DOMNode


# Convert class events to instance events...
# FIXME: there must be a better pattern, also need weakrefs
class _Button(txtwdgs.Button):
    _callbacks: list[WeakCallback] = []

    def on_button_pressed(self):
        for callback in self._callbacks:
            callback(True)


class _Input(txtwdgs.Input):
    _callbacks: list[WeakCallback] = []

    def on_input_changed(self):
        for callback in self._callbacks:
            callback(self.value)


class _Switch(txtwdgs.Switch):
    _callbacks: list[WeakCallback] = []

    def on_switch_changed(self):
        for callback in self._callbacks:
            callback(self.value)


class TxtBaseWidget(protocols.WidgetProtocol):
    """Base Widget Protocol: specifies methods that all widgets must provide."""

    _txwidget: TxWidget

    def __init__(
        self, wdg_class: type[TxWidget] | None = None, parent: TxWidget | None = None
    ):
        if wdg_class is None:
            wdg_class = type(self).__annotations__.get("_txwidget")
        if wdg_class is None:
            raise TypeError("Must provide a valid textual widget type")
        self._txwidget = wdg_class()

        # TODO: here we add the widget to our global app instance... but perhaps
        # we should be using `mount()`?
        MguiApp._mgui_widgets.append(self._txwidget)

        # TODO: assign parent ?

    def _mgui_close_widget(self) -> None:
        """Close widget."""
        # not sure there is a textual equivalent of closing?
        self._mgui_set_visible(False)

    def _mgui_get_visible(self) -> bool:
        """Get widget visibility."""
        return self._txwidget.visible

    def _mgui_set_visible(self, value: bool) -> None:
        """Set widget visibility."""
        self._txwidget.visible = value

    def _mgui_get_enabled(self) -> bool:
        """Get the enabled state of the widget."""
        return not self._txwidget.disabled

    def _mgui_set_enabled(self, enabled: bool) -> None:
        """Set the enabled state of the widget to `enabled`."""
        self._txwidget.disabled = not enabled

    def _mgui_get_parent(self) -> "DOMNode | None":
        """Return the parent widget of this widget."""
        return self._txwidget.parent

    def _mgui_set_parent(self, widget: TxWidget) -> None:
        """Set the parent widget of this widget."""
        raise NotImplementedError("Setting parent of textual widget not supported")

    def _mgui_get_native_widget(self) -> Any:
        """Return the native backend widget instance.

        This is generally the widget that has the layout.
        """
        return self._txwidget

    def _mgui_get_root_native_widget(self) -> Any:
        """Return the root native backend widget.

        In most cases, this is the same as ``_mgui_get_native_widget``.  However, in
        cases where the native widget is in a scroll layout, this might be different.
        """
        return self._txwidget

    def _mgui_bind_parent_change_callback(
        self, callback: Callable[[Any], None]
    ) -> None:
        """Bind callback to parent change event."""
        pass

    def _mgui_render(self) -> "np.ndarray":
        """Return an RGBA (MxNx4) numpy array bitmap of the rendered widget."""
        raise NotImplementedError("Textual widget screenshots not yet implemented")

    def _mgui_get_width(self) -> int:
        """Get the width of the widget.

        The intention is to get the width of the widget after it is shown, for the
        purpose of unifying widget width in a layout. Backends may do what they need to
        accomplish this. For example, Qt can use ``sizeHint().width()``, since
        ``width()`` may return something large if the widget has not yet been painted
        on screen.
        """
        return self._txwidget.styles.width

    def _mgui_set_width(self, value: int) -> None:
        """Set the width of the widget."""
        self._txwidget.styles.width = value

    def _mgui_get_min_width(self) -> int:
        """Get the minimum width of the widget."""
        return self._txwidget.styles.min_width

    def _mgui_set_min_width(self, value: int) -> None:
        """Set the minimum width of the widget."""
        self._txwidget.styles.min_width = value

    def _mgui_get_max_width(self) -> int:
        """Get the maximum width of the widget."""
        return self._txwidget.styles.max_width

    def _mgui_set_max_width(self, value: int) -> None:
        """Set the maximum width of the widget."""
        self._txwidget.styles.max_width = value

    def _mgui_get_height(self) -> int:
        """Get the height of the widget.

        The intention is to get the height of the widget after it is shown, for the
        purpose of unifying widget height in a layout. Backends may do what they need to
        accomplish this. For example, Qt can use ``sizeHint().height()``, since
        ``height()`` may return something large if the widget has not yet been painted
        on screen.
        """
        return self._txwidget.styles.height

    def _mgui_set_height(self, value: int) -> None:
        """Set the height of the widget."""
        self._txwidget.styles.height = value

    def _mgui_get_min_height(self) -> int:
        """Get the minimum height of the widget."""
        return self._txwidget.styles.min_height

    def _mgui_set_min_height(self, value: int) -> None:
        """Set the minimum height of the widget."""
        self._txwidget.styles.min_height = value

    def _mgui_get_max_height(self) -> int:
        """Get the maximum height of the widget."""
        return self._txwidget.styles.max_height

    def _mgui_set_max_height(self, value: int) -> None:
        """Set the maximum height of the widget."""
        self._txwidget.styles.max_height = value

    def _mgui_get_tooltip(self) -> str:
        """Get the tooltip for this widget."""
        return ""

    def _mgui_set_tooltip(self, value: str | None) -> None:
        """Set a tooltip for this widget."""
        pass


class TxtValueWidget(TxtBaseWidget, protocols.ValueWidgetProtocol):
    _txwidget: txtwdgs.Static

    def _mgui_get_value(self) -> Any:
        """Get current value of the widget."""
        return self._txwidget.renderable

    def _mgui_set_value(self, value: Any) -> None:
        """Set current value of the widget."""
        self._txwidget.renderable = value

    def _mgui_bind_change_callback(self, callback: Callable[[Any], Any]) -> None:
        """Bind callback to value change event."""
        if hasattr(self._txwidget, "_callbacks"):
            callbacks = cast("list", self._txwidget._callbacks)
            callbacks.append(weak_callback(callback))


class TxtStringWidget(TxtValueWidget):
    def _mgui_set_value(self, value) -> None:
        super()._mgui_set_value(str(value))


class Label(TxtStringWidget):
    _txwidget: txtwdgs.Label


class LineEdit(TxtStringWidget):
    _txwidget: _Input

    def _mgui_get_value(self) -> Any:
        """Get current value of the widget."""
        return self._txwidget.value

    def _mgui_set_value(self, value: Any) -> None:
        """Set current value of the widget."""
        self._txwidget.value = value


class TxtBaseButtonWidget(TxtValueWidget, protocols.SupportsText):
    _txwidget: _Button

    def _mgui_set_text(self, value: str) -> None:
        """Set text."""
        self._txwidget.label = value

    def _mgui_get_text(self) -> str:
        """Get text."""
        return self._txwidget.label


class PushButton(TxtBaseButtonWidget):
    pass


class CheckBox(TxtBaseButtonWidget):
    _txwidget: _Switch
