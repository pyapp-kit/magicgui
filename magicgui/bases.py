"""Abstract base classes (Interfaces) for backends to implement."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Optional,
    Protocol,
    Tuple,
    runtime_checkable,
)

if TYPE_CHECKING:
    from magicgui.widget import Widget


# Protocols ----------------------------------------------------------------------

# -> BaseWidget
#      - _mg_show_widget
#      - _mg_hide_widget
#      - _mg_get_native_widget
#
#      ↪ BaseValueWidget
#           - _mg_get_value
#           - _mg_set_value
#           - _mg_bind_change_callback
#
#           ↪ BaseRangedWidget
#                - _mg_get_minimum
#                - _mg_set_minimum
#                - _mg_get_maximum
#                - _mg_set_maximum
#                - _mg_get_step
#                - _mg_set_step
#
#           ↪ BaseCategoricalWidget
#                - _mg_get_choices
#                - _mg_set_choices


@runtime_checkable
class BaseWidget(Protocol):
    """All must have show/hide and return the native widget."""

    @abstractmethod
    def _mg_show_widget(self):
        """Show the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_hide_widget(self):
        """Hide the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_enabled(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_enabled(self, enabled: bool):
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_parent(self) -> Widget:
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_parent(self, widget: Widget):
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_native_widget(self):
        raise NotImplementedError()


@runtime_checkable
class BaseValueWidget(BaseWidget, Protocol):
    """Widget that has a current value, with getter/setter and on_change callback."""

    @abstractmethod
    def _mg_get_value(self) -> Any:
        """Get current value of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_value(self, value) -> None:
        """Set current value of the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_bind_change_callback(self, callback: Callable[[Any], None]):
        """Bind callback to value change event."""
        raise NotImplementedError()


# note that "float" type hints also accept ints
# https://www.python.org/dev/peps/pep-0484/#the-numeric-tower
@runtime_checkable
class BaseRangedWidget(BaseValueWidget, Protocol):
    """Value widget that supports numbers within a provided min/max range."""

    @abstractmethod
    def _mg_get_minimum(self) -> float:
        """Get the minimum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_minimum(self, value: float):
        """Set the minimum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_maximum(self) -> float:
        """Get the maximum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_maximum(self, value: float):
        """Set the maximum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_step(self) -> float:
        """Get the step size."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_step(self, value: float):
        """Set the step size."""
        raise NotImplementedError()


@runtime_checkable
class SupportsChoices(Protocol):
    """Widget that has a set of valid choices."""

    @abstractmethod
    def _mg_get_choices(self) -> Tuple[Tuple[str, Any]]:
        """Get available choices."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_choices(self, choices: Iterable[Tuple[str, Any]]):
        """Set available choices."""
        raise NotImplementedError()


@runtime_checkable
class BaseCategoricalWidget(BaseValueWidget, SupportsChoices, Protocol):
    """Categorical widget, that has a set of valid choices, and a current value."""

    pass


class BaseDateTimeWidget(BaseValueWidget):
    """The "value" in a ButtonWidget is the current (checked) state."""


@runtime_checkable
class SupportsText(Protocol):
    """Widget that have text (in addition to value)... like buttons."""

    @abstractmethod
    def _mg_set_text(self, value: str) -> None:
        """Set text."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_text(self) -> str:
        """Get text."""
        raise NotImplementedError()


@runtime_checkable
class BaseButtonWidget(BaseValueWidget, SupportsText, Protocol):
    """The "value" in a ButtonWidget is the current (checked) state."""


# CONTAINER ----------------------------------------------------------------------


@runtime_checkable
class SupportsOrientation(Protocol):
    """Widget that can be reoriented."""

    @property
    def orientation(self):
        """Orientation of the widget."""
        return self._mg_get_orientation()

    @orientation.setter
    def orientation(self, value):
        assert value in {"horizontal", "vertical"}
        self._mg_set_orientation(value)

    @abstractmethod
    def _mg_set_orientation(self, value) -> None:
        """Set orientation, value will be 'horizontal' or 'vertical'."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_orientation(self) -> str:
        """Get orientation, return either 'horizontal' or 'vertical'."""
        raise NotImplementedError()


class BaseContainer(BaseWidget, SupportsOrientation, Protocol):
    """Widget that can contain other widgets."""

    @abstractmethod
    def _mg_add_widget(self, widget: "Widget"):
        raise NotImplementedError()

    @abstractmethod
    def _mg_insert_widget(self, position: int, widget: "Widget"):
        raise NotImplementedError()

    @abstractmethod
    def _mg_remove_widget(self, widget: "Widget"):
        raise NotImplementedError()

    @abstractmethod
    def _mg_remove_index(self, position: int):
        raise NotImplementedError()

    @abstractmethod
    def _mg_count(self) -> int:
        raise NotImplementedError()

    @abstractmethod
    def _mg_index(self, widget: "Widget") -> int:
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_index(self, index: int) -> "Optional[Widget]":
        """(return None instead of index error)."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_native_layout(self) -> Any:
        raise NotImplementedError()


# APPLICATION --------------------------------------------------------------------


class BaseApplicationBackend(ABC):
    """Backend Application object.

    Abstract class that provides an interface between backends and Application.
    Each backend must implement a subclass of BaseApplicationBackend, and
    implement all its _mg_xxx methods.
    """

    @abstractmethod
    def _mg_get_backend_name(self) -> str:
        """Return the name of the backend."""

    @abstractmethod
    def _mg_process_events(self):
        """Process all pending GUI events."""

    @abstractmethod
    def _mg_run(self):
        """Start the application."""

    @abstractmethod
    def _mg_quit(self):
        """Quit the native GUI event loop."""

    def _mg_get_native_app(self):
        """Return the native GUI application instance."""
        return self

    @abstractmethod
    def _mg_start_timer(
        self,
        interval: int = 0,
        on_timeout: Optional[Callable[[], None]] = None,
        single: bool = False,
    ):
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
    def _mg_stop_timer(self):
        """Stop timer.  Should check for the existence of the timer."""
