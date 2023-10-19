from __future__ import annotations

from typing import TYPE_CHECKING, Callable, cast

from ._container_widget import ContainerWidget

if TYPE_CHECKING:
    from magicgui.widgets import protocols
    from magicgui.widgets._concrete import StatusBar

    from ._widget import Widget


class MainWindowWidget(ContainerWidget):
    """Top level Application widget that can contain other widgets."""

    _widget: protocols.MainWindowProtocol
    _status_bar: StatusBar | None = None

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

    def add_dock_widget(
        self, widget: Widget, *, area: protocols.Area = "right"
    ) -> None:
        """Add a dock widget to the main window.

        Parameters
        ----------
        widget : Widget
            The widget to add to the main window.
        area : str, optional
            The area in which to add the widget, must be one of
            `{'left', 'right', 'top', 'bottom'}`, by default "right".
        """
        self._widget._mgui_add_dock_widget(widget, area)

    def add_tool_bar(self, widget: Widget, *, area: protocols.Area = "top") -> None:
        """Add a toolbar to the main window.

        Parameters
        ----------
        widget : Widget
            The widget to add to the main window.
        area : str, optional
            The area in which to add the widget, must be one of
            `{'left', 'right', 'top', 'bottom'}`, by default "top".
        """
        self._widget._mgui_add_tool_bar(widget, area)

    def set_menubar(self, widget: Widget) -> None:
        """Set the menubar of the main window.

        Parameters
        ----------
        widget : Widget
            The widget to add to the main window.
        """
        self._widget._mgui_set_menu_bar(widget)

    @property
    def menu_bar(self) -> StatusBar:
        """Return the status bar widget."""
        if self._status_bar is None:
            from magicgui.widgets._concrete import StatusBar

            self.status_bar = StatusBar()
        return cast("StatusBar", self._status_bar)
    
    # def set_status_bar(self, widget: Widget) -> None:
    #     """Set the statusbar of the main window.

    #     Parameters
    #     ----------
    #     widget : Widget
    #         The widget to add to the main window.
    #     """
    #     self._widget._mgui_set_status_bar(widget)

    @property
    def status_bar(self) -> StatusBar:
        """Return the status bar widget."""
        if self._status_bar is None:
            from magicgui.widgets._concrete import StatusBar

            self.status_bar = StatusBar()
        return cast("StatusBar", self._status_bar)

    @status_bar.setter
    def status_bar(self, widget: StatusBar | None) -> None:
        """Set the status bar widget."""
        self._status_bar = widget
        self._widget._mgui_set_status_bar(widget)
