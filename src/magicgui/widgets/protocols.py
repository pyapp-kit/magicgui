"""Protocols (interfaces) for backends to implement.

Each class in this module is a [typing.Protocol][typing.Protocol] that specifies
a set of :func:`~abc.abstractmethod` that a backend widget must implement
to be compatible with the magicgui API.
All magicgui-specific abstract methods are prefaced with ``_mgui_*``.

For an example backend implementation, see ``magicgui.backends._qtpy.widgets``
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    NoReturn,
    Protocol,
    Sequence,
    runtime_checkable,
)

if TYPE_CHECKING:
    import numpy as np

    from magicgui.widgets.bases import Widget


def assert_protocol(widget_class: type, protocol: type) -> None:
    """Ensure that widget_class implements protocol, or raise helpful error."""
    if not isinstance(widget_class, protocol):
        _raise_protocol_error(widget_class, protocol)
    return None


def _raise_protocol_error(widget_class: type, protocol: type) -> NoReturn:
    """Raise a more helpful error when required protocol members are missing."""
    missing = {
        i
        for i in set(dir(protocol)) - set(dir(widget_class))
        if not i.startswith(("__", "_is_protocol", "_is_runtime", "_abc_impl"))
    }
    message = (
        f"{widget_class!r} does not implement {protocol.__name__!r}.\n"
        f"Missing methods: {missing!r}"
    )
    raise TypeError(message)


@runtime_checkable
class WidgetProtocol(Protocol):
    """Base Widget Protocol: specifies methods that all widgets must provide."""

    def __init__(self, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def _mgui_close_widget(self) -> None:
        """Close widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_visible(self) -> bool:
        """Get widget visibility."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_visible(self, value: bool) -> None:
        """Set widget visibility."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_enabled(self) -> bool:
        """Get the enabled state of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_enabled(self, enabled: bool) -> None:
        """Set the enabled state of the widget to `enabled`."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_parent(self) -> Widget:
        """Return the parent widget of this widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_parent(self, widget: Widget) -> None:
        """Set the parent widget of this widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_native_widget(self) -> Any:
        """Return the native backend widget instance.

        This is generally the widget that has the layout.
        """
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_root_native_widget(self) -> Any:
        """Return the root native backend widget.

        In most cases, this is the same as ``_mgui_get_native_widget``.  However, in
        cases where the native widget is in a scroll layout, this might be different.
        """
        raise NotImplementedError()

    @abstractmethod
    def _mgui_bind_parent_change_callback(
        self, callback: Callable[[Any], None]
    ) -> None:
        """Bind callback to parent change event."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_render(self) -> np.ndarray:
        """Return an RGBA (MxNx4) numpy array bitmap of the rendered widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_width(self) -> int:
        """Get the width of the widget.

        The intention is to get the width of the widget after it is shown, for the
        purpose of unifying widget width in a layout. Backends may do what they need to
        accomplish this. For example, Qt can use ``sizeHint().width()``, since
        ``width()`` may return something large if the widget has not yet been painted
        on screen.
        """
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_width(self, value: int) -> None:
        """Set the width of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_min_width(self) -> int:
        """Get the minimum width of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_min_width(self, value: int) -> None:
        """Set the minimum width of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_max_width(self) -> int:
        """Get the maximum width of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_max_width(self, value: int) -> None:
        """Set the maximum width of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_height(self) -> int:
        """Get the height of the widget.

        The intention is to get the height of the widget after it is shown, for the
        purpose of unifying widget height in a layout. Backends may do what they need to
        accomplish this. For example, Qt can use ``sizeHint().height()``, since
        ``height()`` may return something large if the widget has not yet been painted
        on screen.
        """
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_height(self, value: int) -> None:
        """Set the height of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_min_height(self) -> int:
        """Get the minimum height of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_min_height(self, value: int) -> None:
        """Set the minimum height of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_max_height(self) -> int:
        """Get the maximum height of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_max_height(self, value: int) -> None:
        """Set the maximum height of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_tooltip(self) -> str:
        """Get the tooltip for this widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_tooltip(self, value: str | None) -> None:
        """Set a tooltip for this widget."""
        raise NotImplementedError()


@runtime_checkable
class ValueWidgetProtocol(WidgetProtocol, Protocol):
    """Widget that has a current value, with getter/setter and on_change callback.

    It is worth noting that the **widget** is the thing that has a value.  Magicgui
    does not maintain & synchronize an independent model.
    """

    @abstractmethod
    def _mgui_get_value(self) -> Any:
        """Get current value of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_value(self, value: Any) -> None:
        """Set current value of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_bind_change_callback(self, callback: Callable[[Any], Any]) -> None:
        """Bind callback to value change event."""
        raise NotImplementedError()


@runtime_checkable
class SupportsReadOnly(Protocol):
    """Widget that can be read_only."""

    @abstractmethod
    def _mgui_set_read_only(self, value: bool) -> None:
        """Set read_only."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_read_only(self) -> bool:
        """Get read_only status."""
        raise NotImplementedError()


@runtime_checkable
class TableWidgetProtocol(ValueWidgetProtocol, SupportsReadOnly, Protocol):
    """ValueWidget subclass intended for 2D tabular data, with row & column headers."""

    @abstractmethod
    def _mgui_get_row_count(self) -> int:
        """Get the number of rows in the table."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_row_count(self, nrows: int) -> None:
        """Set the number of rows in the table. (Create/delete as needed)."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_remove_row(self, row: int) -> None:
        """Remove row at index `row`."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_column_count(self) -> int:
        """Get the number of columns in the table."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_column_count(self, ncols: int) -> None:
        """Set the number of columns in the table. (Create/delete as needed)."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_remove_column(self, column: int) -> None:
        """Remove column at index `column`."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_cell(self, row: int, col: int) -> Any:
        """Get current value of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_cell(self, row: int, col: int, value: Any) -> None:
        """Set current value of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_row_headers(self) -> tuple:
        """Get current row headers of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_row_headers(self, headers: Sequence) -> None:
        """Set current row headers of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_column_headers(self) -> tuple:
        """Get current column headers of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_column_headers(self, headers: Sequence) -> None:
        """Set current column headers of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_bind_row_headers_change_callback(
        self, callback: Callable[[Any], None]
    ) -> None:
        """Bind callback to row headers change event."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_bind_column_headers_change_callback(
        self, callback: Callable[[Any], None]
    ) -> None:
        """Bind callback to column headers change event."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_bind_change_callback(self, callback: Callable[[Any], Any]) -> None:
        """Bind callback to value change event."""
        raise NotImplementedError()


# note that "float" type hints also accept ints
# https://www.python.org/dev/peps/pep-0484/#the-numeric-tower
@runtime_checkable
class RangedWidgetProtocol(ValueWidgetProtocol, Protocol):
    """Value widget that supports numbers within a provided min/max range."""

    @abstractmethod
    def _mgui_get_min(self) -> float:
        """Get the minimum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_min(self, value: float) -> None:
        """Set the minimum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_max(self) -> float:
        """Get the maximum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_max(self, value: float) -> None:
        """Set the maximum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_step(self) -> float:
        """Get the step size."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_step(self, value: float) -> None:
        """Set the step size."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_adaptive_step(self) -> bool:
        """Get adaptive step status."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_adaptive_step(self, value: bool) -> None:
        """Set adaptive step status."""
        raise NotImplementedError()


@runtime_checkable
class SupportsChoices(Protocol):
    """Widget that has a set of valid choices."""

    @abstractmethod
    def _mgui_get_choices(self) -> tuple[tuple[str, Any], ...]:
        """Get available choices."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_choices(self, choices: Iterable[tuple[str, Any]]) -> None:
        """Set available choices."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_current_choice(self) -> str:
        """Return the text of the currently selected choice."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_choice(self, choice_name: str) -> Any:
        """Get data for a single choice."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_choice(self, choice_name: str, data: Any) -> None:
        """Set data for choice_name, or add a new item if choice_name doesn't exist."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_del_choice(self, choice_name: str) -> None:
        """Delete the provided ``choice_name`` and associated data."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_count(self) -> int:
        """Return number of choices."""
        raise NotImplementedError


@runtime_checkable
class CategoricalWidgetProtocol(ValueWidgetProtocol, SupportsChoices, Protocol):
    """Categorical widget, that has a set of valid choices, and a current value.

    It adds no additional methods.
    """


@runtime_checkable
class SupportsText(Protocol):
    """Widget that have text (in addition to value)... like buttons."""

    @abstractmethod
    def _mgui_set_text(self, value: str) -> None:
        """Set text."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_text(self) -> str:
        """Get text."""
        raise NotImplementedError()


@runtime_checkable
class SupportsIcon(Protocol):
    """Widget that can be reoriented."""

    @abstractmethod
    def _mgui_set_icon(self, value: str | None, color: str | None) -> None:
        """Set icon.

        Value is an "prefix:name" from iconify: https://icon-sets.iconify.design
        Color is any valid CSS color string.
        Set value to `None` or an empty string to remove icon.
        """


@runtime_checkable
class ButtonWidgetProtocol(ValueWidgetProtocol, SupportsText, SupportsIcon, Protocol):
    """The "value" in a ButtonWidget is the current (checked) state."""


@runtime_checkable
class SupportsOrientation(Protocol):
    """Widget that can be reoriented."""

    @abstractmethod
    def _mgui_set_orientation(self, value: str) -> None:
        """Set orientation, value will be 'horizontal' or 'vertical'."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_orientation(self) -> str:
        """Get orientation, return either 'horizontal' or 'vertical'."""
        raise NotImplementedError()


@runtime_checkable
class SliderWidgetProtocol(RangedWidgetProtocol, SupportsOrientation, Protocol):
    """Protocol for implementing a slider widget."""

    def _mgui_set_readout_visibility(self, visible: bool) -> None:
        """Set visibility of readout widget."""

    def _mgui_get_tracking(self) -> bool:
        """If tracking is False, changed is only emitted when released."""

    def _mgui_set_tracking(self, tracking: bool) -> None:
        """If tracking is False, changed is only emitted when released."""


# CONTAINER ----------------------------------------------------------------------


class ContainerProtocol(WidgetProtocol, SupportsOrientation, Protocol):
    """Widget that can contain other widgets.

    This generally manages a backend Layout.
    """

    @abstractmethod
    def _mgui_insert_widget(self, position: int, widget: Widget) -> None:
        """Insert `widget` at the given `position` in the layout."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_remove_widget(self, widget: Widget) -> None:
        """Remove the specified widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_margins(self) -> tuple[int, int, int, int]:
        """Get the margins of the container."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_margins(self, margins: tuple[int, int, int, int]) -> None:
        """Set the margins of the container."""
        raise NotImplementedError()


@runtime_checkable
class ToolBarProtocol(WidgetProtocol, Protocol):
    """Toolbar that contains a set of controls."""

    @abstractmethod
    def _mgui_add_button(
        self, text: str, icon: str, callback: Callable | None = None
    ) -> None:
        """Add a button to the toolbar."""

    @abstractmethod
    def _mgui_add_separator(self) -> None:
        """Add a separator line to the toolbar."""

    @abstractmethod
    def _mgui_add_spacer(self) -> None:
        """Add a spacer to the toolbar."""

    @abstractmethod
    def _mgui_add_widget(self, widget: Widget) -> None:
        """Add a widget to the toolbar."""

    @abstractmethod
    def _mgui_get_icon_size(self) -> tuple[int, int] | None:
        """Return the icon size of the toolbar."""

    @abstractmethod
    def _mgui_set_icon_size(self, size: int | tuple[int, int] | None) -> None:
        """Set the icon size of the toolbar."""

    @abstractmethod
    def _mgui_clear(self) -> None:
        """Clear the toolbar."""


class DialogProtocol(ContainerProtocol, Protocol):
    """Protocol for modal (blocking) containers."""

    @abstractmethod
    def _mgui_exec(self) -> None:
        """Show the dialog and block."""
        raise NotImplementedError()


class MainWindowProtocol(ContainerProtocol, Protocol):
    """Application main widget."""

    @abstractmethod
    def _mgui_create_menu_item(
        self,
        menu_name: str,
        action_name: str,
        callback: Callable | None = None,
        shortcut: str | None = None,
    ) -> None:
        """Create a new menu item.

        Parameters
        ----------
        menu_name : str
            The name of the menu to add the item to.
        action_name : str
            The name of the action to add.
        callback : Callable | None, optional
            A callback to be called when the action is triggered, by default None.
        shortcut : str | None, optional
            A keyboard shortcut for the action, by default None.
        """
        raise NotImplementedError()


# APPLICATION --------------------------------------------------------------------


class BaseApplicationBackend(ABC):
    """Backend Application object.

    Abstract class that provides an interface between backends and `Application`.
    Each backend must implement a subclass of `BaseApplicationBackend`, and
    implement all of its `_mgui_xxx` methods.
    """

    @abstractmethod
    def _mgui_get_backend_name(self) -> str:
        """Return the name of the backend."""

    @abstractmethod
    def _mgui_process_events(self) -> None:
        """Process all pending GUI events."""

    @abstractmethod
    def _mgui_run(self) -> None:
        """Start the application."""

    @abstractmethod
    def _mgui_quit(self) -> None:
        """Quit the native GUI event loop."""

    @abstractmethod
    def _mgui_get_native_app(self) -> Any:
        """Return the native GUI application instance."""

    @abstractmethod
    def _mgui_start_timer(
        self,
        interval: int = 0,
        on_timeout: Callable[[], None] | None = None,
        single: bool = False,
    ) -> None:
        """Create and start a timer.

        Parameters
        ----------
        interval : int, optional
            Interval between timeouts, by default 0
        on_timeout : Optional[Callable[[], None]], optional
            Function to call when timer finishes, by default None
        single : bool, optional
            Whether the timer should only fire once, by default False
        """

    @abstractmethod
    def _mgui_stop_timer(self) -> None:
        """Stop timer.  Should check for the existence of the timer."""
