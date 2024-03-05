from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, overload

from ._widget import Widget

if TYPE_CHECKING:
    from magicgui.widgets import protocols
    from magicgui.widgets._concrete import Menu


class _SupportsMenus:
    """Mixin for widgets that support menus."""

    _widget: protocols.MenuBarProtocol | protocols.MenuProtocol

    def __init__(self, *args: Any, **kwargs: Any):
        self._menus: dict[str, MenuWidget] = {}
        super().__init__(*args, **kwargs)

    def __getitem__(self, key: str) -> MenuWidget:
        return self._menus[key]

    @overload
    def add_menu(self, widget: Menu) -> MenuWidget:
        ...

    @overload
    def add_menu(self, title: str, icon: str | None = None) -> MenuWidget:
        ...

    def add_menu(
        self,
        *args: Any,
        widget: Menu | None = None,
        title: str = "",
        icon: str | None = None,
    ) -> MenuWidget:
        """Add a menu to the menu bar."""
        widget = _parse_menu_overload(args, widget, title, icon)
        self._menus[widget.title] = widget
        self._widget._mgui_add_menu_widget(widget)
        return widget


def _parse_menu_overload(
    args: tuple, widget: Menu | None = None, title: str = "", icon: str | None = None
) -> Menu:
    from magicgui.widgets._concrete import Menu

    if len(args) == 2:
        title, icon = args
    elif len(args) == 1:
        if not isinstance(arg0 := args[0], (str, Menu)):
            raise TypeError("First argument must be a string or Menu")
        if isinstance(arg0, Menu):
            widget = arg0
        else:
            title = arg0

    if widget is None:
        widget = Menu(title=title, icon=icon)
    return widget


class MenuBarWidget(_SupportsMenus, Widget):
    """Menu bar containing menus. Can be added to a MainWindowWidget."""

    _widget: protocols.MenuBarProtocol

    def __init__(self, **base_widget_kwargs: Any) -> None:
        super().__init__(**base_widget_kwargs)

    def clear(self) -> None:
        """Clear the menu bar."""
        self._widget._mgui_clear()


class MenuWidget(_SupportsMenus, Widget):
    """Menu widget. Can be added to a MenuBarWidget or another MenuWidget."""

    _widget: protocols.MenuProtocol

    def __init__(
        self, title: str = "", icon: str | None = "", **base_widget_kwargs: Any
    ) -> None:
        super().__init__(**base_widget_kwargs)
        self.title = title
        self.icon = icon

    @property
    def title(self) -> str:
        """Title of the menu."""
        return self._widget._mgui_get_title()

    @title.setter
    def title(self, value: str) -> None:
        self._widget._mgui_set_title(value)

    @property
    def icon(self) -> str | None:
        """Icon of the menu."""
        return self._widget._mgui_get_icon()

    @icon.setter
    def icon(self, value: str | None) -> None:
        self._widget._mgui_set_icon(value)

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

    def clear(self) -> None:
        """Clear the menu."""
        self._widget._mgui_clear()
