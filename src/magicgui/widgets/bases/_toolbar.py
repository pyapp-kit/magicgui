from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Tuple, TypeVar, Union

from ._widget import Widget

if TYPE_CHECKING:
    from magicgui.widgets import protocols

T = TypeVar("T", int, float, Tuple[Union[int, float], ...])
DEFAULT_MIN = 0.0
DEFAULT_MAX = 1000.0


class ToolBarWidget(Widget):
    """Widget with a value, Wraps ValueWidgetProtocol.

    Parameters
    ----------
    **base_widget_kwargs : Any
        All additional keyword arguments are passed to the base
        [`magicgui.widgets.Widget`][magicgui.widgets.Widget] constructor.
    """

    _widget: protocols.ToolBarProtocol

    def __init__(self, **base_widget_kwargs: Any) -> None:
        super().__init__(**base_widget_kwargs)

    def add_button(
        self, text: str = "", icon: str = "", callback: Callable | None = None
    ) -> None:
        """Add an action to the toolbar."""
        self._widget._mgui_add_button(text, icon, callback)

    def add_separator(self) -> None:
        """Add a separator line to the toolbar."""
        self._widget._mgui_add_separator()

    def add_spacer(self) -> None:
        """Add a spacer to the toolbar."""
        self._widget._mgui_add_spacer()

    def add_widget(self, widget: Widget) -> None:
        """Add a widget to the toolbar."""
        self._widget._mgui_add_widget(widget)

    @property
    def icon_size(self) -> tuple[int, int] | None:
        """Return the icon size of the toolbar."""
        return self._widget._mgui_get_icon_size()

    @icon_size.setter
    def icon_size(self, size: int | tuple[int, int] | None) -> None:
        """Set the icon size of the toolbar."""
        self._widget._mgui_set_icon_size(size)

    def clear(self) -> None:
        """Clear the toolbar."""
        self._widget._mgui_clear()
