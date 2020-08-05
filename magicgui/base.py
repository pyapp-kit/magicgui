"""Abstract base classes (Interfaces) for backends to implement."""
from __future__ import annotations

from abc import ABC, abstractmethod

from typing import (
    Callable,
    Optional,
    Any,
    Iterable,
    TypedDict,
    Tuple,
    Union,
    Protocol,
    runtime_checkable,
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from magicgui.widget import Widget

Number = Union[int, float]

# TODO: organize something other than strings
WIDGETS = {
    # Buttons
    "CheckBox",
    "PushButton",
    "RadioButton",
    "ToolButton",
    # Numbers
    "SpinBox",
    "FloatSpinBox",
    "Slider",
    "LogSlider"
    # Strings
    "LineEdit",
    "TextEdit",
    "Label",
    # Status
    "StatusBar",
    # Dates
    "DateTimeWidget",
    "DateWidget",
    "TimeWidget",
    # Choices
    "ComboBox",
    "Listbox",
    # Container
    "GroupBox",
}


class BaseWidget(ABC):
    def __init__(self, mg_widget: "Widget"):
        self._mg_widget = mg_widget

    # INTERFACE ------------------------------

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

    @abstractmethod
    def _mg_get_native_widget(self):
        raise NotImplementedError()

    @abstractmethod
    def _mg_show_widget(self):
        """Show the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_hide_widget(self):
        """Hide the widget."""
        raise NotImplementedError()


class BaseNumberWidget(BaseWidget, ABC):
    @property
    def minimum(self) -> Number:
        return self._mg_get_minimum()

    @minimum.setter
    def minimum(self, value: Number):
        self._mg_set_minimum(value)

    @property
    def maximum(self) -> Number:
        return self._mg_get_maximum()

    @maximum.setter
    def maximum(self, value: Number):
        self._mg_set_maximum(value)

    @property
    def step(self) -> Number:
        return self._mg_get_step()

    @step.setter
    def step(self, value: Number):
        self._mg_set_step(value)

    @property
    def range(self) -> Tuple[Number, Number]:
        return self._mg_get_range()

    @range.setter
    def range(self, value: Tuple[Number, Number]):
        self._mg_set_range(value)

    # INTERFACE ------------------------------

    @abstractmethod
    def _mg_get_minimum(self) -> Number:
        """Get the minimum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_minimum(self, value: Number):
        """Set the minimum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_maximum(self) -> Number:
        """Get the maximum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_maximum(self, value: Number):
        """Set the maximum possible value."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_step(self) -> Number:
        """Get the step size."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_step(self, value: Number):
        """Set the step size."""
        raise NotImplementedError()

    def _mg_set_range(self, value: Tuple[Number, Number]):
        """Set the step size."""
        self._mg_set_minimum(value[0])
        self._mg_set_maximum(value[1])

    def _mg_get_range(self) -> Tuple[Number, Number]:
        """Set the step size."""
        return self._mg_get_minimum(), self._mg_get_maximum()


@runtime_checkable
class SupportsOrientation(Protocol):
    @property
    def orientation(self):
        return self._mg_get_orientation()

    @orientation.setter
    def orientation(self, value):
        assert value in {"horizontal", "vertical"}
        self._mg_set_orientation(value)

    # INTERFACE ------------------------------

    @abstractmethod
    def _mg_set_orientation(self, value) -> None:
        """Set orientation, value will be 'horizontal' or 'vertical'"""
        raise NotImplementedError()

    @abstractmethod
    def _mg_get_orientation(self) -> str:
        """Set orientation, return either 'horizontal' or 'vertical'"""
        raise NotImplementedError()


class ChoicesDict(TypedDict):
    choices: Union[Iterable[Tuple[str, Any]], Iterable[Any]]
    key: Callable[[Any], str]


@runtime_checkable
class SupportsChoices(Protocol):
    @property
    def choices(self):
        return tuple(i[0] for i in self._mg_get_choices())

    @choices.setter
    def choices(
        self, choices: Union[Iterable[Tuple[str, Any]], Iterable[Any], ChoicesDict],
    ):
        str_func: Callable = str
        if isinstance(choices, dict):
            if not ("choices" in choices and "key" in choices):
                raise ValueError(
                    "When setting choices with a dict, the dict must have keys "
                    "'choices' (Iterable), and 'key' (callable that takes a each value "
                    "in `choices` and returns a string."
                )
            _choices = choices["choices"]
            str_func = choices["key"]
        else:
            _choices = choices
        if not all(isinstance(i, tuple) and len(i) == 2 for i in _choices):
            _choices = [(str_func(i), i) for i in _choices]
        return self._mg_set_choices(_choices)

    # INTERFACE ------------------------------

    @abstractmethod
    def _mg_get_choices(self) -> Tuple[Tuple[str, Any]]:
        """Show the widget."""
        raise NotImplementedError()

    @abstractmethod
    def _mg_set_choices(self, choices: Iterable[Tuple[str, Any]]):
        """Show the widget."""
        raise NotImplementedError()


class BaseApplicationBackend(ABC):
    """BaseApplicationBackend()

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


class BaseLayout(SupportsOrientation, ABC):
    """Base layout interface."""

    # INTERFACE ------------------------------

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
