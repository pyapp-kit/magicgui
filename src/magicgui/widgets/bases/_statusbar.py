from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._widget import Widget

if TYPE_CHECKING:
    from magicgui.widgets import protocols


class StatusBarWidget(Widget):
    """Widget with a value, Wraps ValueWidgetProtocol.

    Parameters
    ----------
    **base_widget_kwargs : Any
        All additional keyword arguments are passed to the base
        [`magicgui.widgets.Widget`][magicgui.widgets.Widget] constructor.
    """

    _widget: protocols.StatusBarProtocol

    def __init__(self, **base_widget_kwargs: Any) -> None:
        super().__init__(**base_widget_kwargs)

    def add_widget(self, widget: Widget) -> None:
        """Add a widget to the toolbar."""
        self.insert_widget(-1, widget)

    def insert_widget(self, position: int, widget: Widget) -> None:
        """Insert a widget at the given position."""
        self._widget._mgui_insert_widget(position, widget)

    def remove_widget(self, widget: Widget) -> None:
        """Remove a widget from the toolbar."""
        self._widget._mgui_remove_widget(widget)

    @property
    def message(self) -> str:
        """Return currently shown message, or empty string if None."""
        return self._widget._mgui_get_message()

    @message.setter
    def message(self, message: str) -> None:
        """Return the message timeout in milliseconds."""
        self.set_message(message)

    def set_message(self, message: str, timeout: int = 0) -> None:
        """Show a message in the status bar for a given timeout.

        To clear the message, set it to the empty string
        """
        self._widget._mgui_set_message(message, timeout)
