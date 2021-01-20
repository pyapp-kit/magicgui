from abc import ABC, abstractmethod
from typing import Tuple
from warnings import warn

from magicgui.widgets import _protocols

from .value_widget import ValueWidget


class RangedWidget(ValueWidget):
    """Widget with a contstrained value. Wraps RangedWidgetProtocol.

    Parameters
    ----------
    min : float, optional
        The minimum allowable value, by default 0
    max : float, optional
        The maximum allowable value, by default 100
    step : float, optional
        The step size for incrementing the value, by default 1
    """

    _widget: _protocols.RangedWidgetProtocol

    def __init__(self, min: float = 0, max: float = 100, step: float = 1, **kwargs):
        for key in ("maximum", "minimum"):
            if key in kwargs:
                warn(
                    f"The {key!r} keyword arguments has been changed to {key[:3]!r}. "
                    "In the future this will raise an exception\n",
                    FutureWarning,
                )
                if key == "maximum":
                    max = kwargs.pop(key)
                else:
                    min = kwargs.pop(key)

        super().__init__(**kwargs)

        self.min = min
        self.max = max
        self.step = step

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        d = super().options.copy()
        d.update({"min": self.min, "max": self.max, "step": self.step})
        return d

    @property
    def min(self) -> float:
        """Minimum allowable value for the widget."""
        return self._widget._mgui_get_min()

    @min.setter
    def min(self, value: float):
        self._widget._mgui_set_min(value)

    @property
    def max(self) -> float:
        """Maximum allowable value for the widget."""
        return self._widget._mgui_get_max()

    @max.setter
    def max(self, value: float):
        self._widget._mgui_set_max(value)

    @property
    def step(self) -> float:
        """Step size for widget values."""
        return self._widget._mgui_get_step()

    @step.setter
    def step(self, value: float):
        self._widget._mgui_set_step(value)

    @property
    def range(self) -> Tuple[float, float]:
        """Range of allowable values for the widget."""
        return self.min, self.max

    @range.setter
    def range(self, value: Tuple[float, float]):
        self.min, self.max = value


class TransformedRangedWidget(RangedWidget, ABC):
    """Widget with a contstrained value. Wraps RangedWidgetProtocol.

    This can be used to map one domain of numbers onto another, useful for creating
    things like LogSliders.  Subclasses must reimplement ``_value_from_position`` and
    ``_position_from_value``.

    Parameters
    ----------
    min : float, optional
        The minimum allowable value, by default 0
    max : float, optional
        The maximum allowable value, by default 100
    min_pos : float, optional
        The minimum value for the *internal* (widget) position, by default 0.
    max_pos : float, optional
        The maximum value for the *internal* (widget) position, by default 0.
    step : float, optional
        The step size for incrementing the value, by default 1
    """

    _widget: _protocols.RangedWidgetProtocol

    def __init__(
        self,
        min: float = 0,
        max: float = 100,
        min_pos: int = 0,
        max_pos: int = 100,
        step: int = 1,
        **kwargs,
    ):
        self._min = min
        self._max = max
        self._min_pos = min_pos
        self._max_pos = max_pos
        ValueWidget.__init__(self, **kwargs)

        self._widget._mgui_set_min(self._min_pos)
        self._widget._mgui_set_max(self._max_pos)
        self._widget._mgui_set_step(step)

    # Just a linear scaling example.
    # Replace _value_from_position, and _position_from_value in subclasses
    # to implement more complex value->position lookups
    @property
    def _scale(self):
        """Slope of a linear map.  Just used as an example."""
        return (self.max - self.min) / (self._max_pos - self._min_pos)

    @abstractmethod
    def _value_from_position(self, position):
        """Return 'real' value given internal widget position."""
        return self.min + self._scale * (position - self._min_pos)

    @abstractmethod
    def _position_from_value(self, value):
        """Return internal widget position given 'real' value."""
        return (value - self.min) / self._scale + self._min_pos

    #########

    @property
    def value(self):
        """Return current value of the widget."""
        return self._value_from_position(self._widget._mgui_get_value())

    @value.setter
    def value(self, value):
        return self._widget._mgui_set_value(self._position_from_value(value))

    @property
    def min(self) -> float:
        """Minimum allowable value for the widget."""
        return self._min

    @min.setter
    def min(self, value: float):
        prev = self.value
        self._min = value
        self.value = prev

    @property
    def max(self) -> float:
        """Maximum allowable value for the widget."""
        return self._max

    @max.setter
    def max(self, value: float):
        prev = self.value
        self._max = value
        self.value = prev
