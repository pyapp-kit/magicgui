from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ._widget import Widget

if TYPE_CHECKING:
    from magicgui.widgets import protocols


class MenuBarWidget(Widget):
    """Menu bar containing menus. Can be added to a MainWindowWidget."""

    _widget: protocols.MenuBarProtocol

    def __init__(self, **base_widget_kwargs: Any) -> None:
        super().__init__(**base_widget_kwargs)
        self._menus: dict[str, MenuWidget] = {}

    def __getitem__(self, key: str) -> MenuWidget:
        return self._menus[key]

    def add_menu(self, title: str, icon: str | None = None) -> MenuWidget:
        """Add a menu to the menu bar."""
        menu_widg = self._widget._mgui_add_menu(title, icon)
        self._menus[title] = wrapped = MenuWidget(widget_type=menu_widg)
        return wrapped

    def clear(self) -> None:
        """Clear the menu bar."""
        self._widget._mgui_clear()


class MenuWidget(Widget):
    """Menu widget. Can be added to a MenuBarWidget or another MenuWidget."""

    _widget: protocols.MenuProtocol

    def __init__(self, **base_widget_kwargs: Any) -> None:
        super().__init__(**base_widget_kwargs)
        self._menus: dict[str, MenuWidget] = {}

    def add_action(
        self,
        text: str,
        shortcut: str | None = None,
        icon: str | None = None,
        tooltip: str | None = None,
        callback: Callable | None = None,
    ) -> None:
        """Add an action to the menu."""
        self._widget._mgui_add_action(text, shortcut, icon, tooltip, callback)

    def add_separator(self) -> None:
        """Add a separator line to the menu."""
        self._widget._mgui_add_separator()

    def add_menu(self, title: str, icon: str | None = None) -> MenuWidget:
        """Add a menu to the menu."""
        menu_widg = self._widget._mgui_add_menu(title, icon)
        self._menus[title] = wrapped = MenuWidget(widget_type=menu_widg)
        return wrapped

    def clear(self) -> None:
        """Clear the menu bar."""
        self._widget._mgui_clear()
