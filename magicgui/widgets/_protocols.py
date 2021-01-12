"""Protocols (interfaces) for backends to implement.

Each class in this module is a :class:`typing.Protocol` that specifies a set of
:func:`~abc.abstractmethod` that a backend widget must implement to be compatible with
the magicgui API.  All magicgui-specific abstract methods are prefaced with ``_mgui_*``.

For an example backend implementation, see ``magicgui.backends._qtpy.widgets``
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional, Tuple, Type

from typing_extensions import Protocol, runtime_checkable

if TYPE_CHECKING:
    import numpy as np

    from magicgui.widgets._bases import Widget


def assert_protocol(widget_class: Type, protocol: Type):
    """Ensure that widget_class implements protocol, or raise helpful error."""
    if not isinstance(widget_class, protocol):
        _raise_protocol_error(widget_class, protocol)


def _raise_protocol_error(widget_class: Type, protocol: Type):
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

    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def _mgui_show_widget(self) -> None:
        """Show the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_hide_widget(self) -> None:
        """Hide the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_enabled(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_enabled(self, enabled: bool) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_parent(self) -> Widget:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_parent(self, widget: Widget) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_native_widget(self) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_bind_parent_change_callback(
        self, callback: Callable[[Any], None]
    ) -> None:
        """Bind callback to parent change event."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_render(self) -> "np.ndarray":
        """Return an RGBA (MxNx4) numpy array bitmap of the rendered widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_width(self) -> int:
        """Return the current width of the widget.

        The naming of this method may change. The intention is to get the width of the
        widget after it is shown, for the purpose of unifying widget width in a layout.
        Backends may do what they need to accomplish this. For example, Qt can use
        ``sizeHint().width()``, since ``width()`` will return something large if the
        widget has not yet been painted on screen.
        """
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_min_width(self, value: int) -> None:
        """Set the width of the widget."""
        raise NotImplementedError()


@runtime_checkable
class ValueWidgetProtocol(WidgetProtocol, Protocol):
    """Widget that has a current value, with getter/setter and on_change callback."""

    @abstractmethod
    def _mgui_get_value(self) -> Any:
        """Get current value of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_value(self, value) -> None:
        """Set current value of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_bind_change_callback(self, callback: Callable[[Any], None]) -> None:
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


@runtime_checkable
class SupportsChoices(Protocol):
    """Widget that has a set of valid choices."""

    @abstractmethod
    def _mgui_get_choices(self) -> Tuple[Tuple[str, Any]]:
        """Get available choices."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_choices(self, choices: Iterable[Tuple[str, Any]]) -> None:
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
    """Categorical widget, that has a set of valid choices, and a current value."""

    pass


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
class ButtonWidgetProtocol(ValueWidgetProtocol, SupportsText, Protocol):
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


# CONTAINER ----------------------------------------------------------------------


class ContainerProtocol(WidgetProtocol, SupportsOrientation, Protocol):
    """Widget that can contain other widgets."""

    @abstractmethod
    def _mgui_add_widget(self, widget: "Widget") -> None:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_insert_widget(self, position: int, widget: "Widget") -> None:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_remove_widget(self, widget: "Widget") -> None:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_remove_index(self, position: int) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_count(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_index(self, widget: "Widget") -> int:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_index(self, index: int) -> Optional[Widget]:
        """(return None instead of index error)."""
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_native_layout(self) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_get_margins(self) -> Tuple[int, int, int, int]:
        raise NotImplementedError()

    @abstractmethod
    def _mgui_set_margins(self, margins: Tuple[int, int, int, int]) -> None:
        raise NotImplementedError()


# APPLICATION --------------------------------------------------------------------


class BaseApplicationBackend(ABC):
    """Backend Application object.

    Abstract class that provides an interface between backends and Application.
    Each backend must implement a subclass of BaseApplicationBackend, and
    implement all its _mgui_xxx methods.
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
        on_timeout: Optional[Callable[[], None]] = None,
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
