import builtins
from abc import ABC, abstractmethod
from math import ceil, log10
from typing import Iterable, Tuple, Union, cast
from warnings import warn

from magicgui.widgets import _protocols

from .value_widget import UNSET, ValueWidget, _Unset

DEFAULT_MIN = 0.0
DEFAULT_MAX = 1000.0


class RangedWidget(ValueWidget):
    """Widget with a constrained value. Wraps RangedWidgetProtocol.

    Parameters
    ----------
    min : float, optional
        The minimum allowable value, by default 0 (or `value` if `value` is less than 0)
    max : float, optional
        The maximum allowable value, by default 999 (or `value` if `value` is greater
        than 999)
    step : float, optional
        The step size for incrementing the value, by default adaptive step is used
    """

    _widget: _protocols.RangedWidgetProtocol

    def __init__(
        self,
        min: Union[float, _Unset] = UNSET,
        max: Union[float, _Unset] = UNSET,
        step: Union[float, _Unset, None] = UNSET,
        **kwargs,
    ):  # sourcery skip: avoid-builtin-shadow
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
        # value should be set *after* min max is set
        val = kwargs.pop("value", UNSET)
        super().__init__(**kwargs)

        if step is UNSET or step is None:
            self.step = None
            self._widget._mgui_set_step(1)
        else:
            self.step = cast(float, step)

        self.min, self.max = self._init_range(val, min, max)
        if val not in (UNSET, None):
            self.value = val

    def _init_range(
        self,
        value: Union[float, Tuple[float, ...]],
        min: Union[float, _Unset],
        max: Union[float, _Unset],
    ) -> Tuple[float, float]:
        """Return min and max based on given value and arguments.

        If min or max are unset, constrain so the given value is within the range.
        """
        val = value if isinstance(value, tuple) else (value,)
        tmp_val = tuple(float(v) if v not in (UNSET, None) else 1 for v in val)

        new_min: float = (
            cast("float", min)
            if min is not UNSET
            else builtins.min(DEFAULT_MIN, *tmp_val)
        )

        if max is UNSET:
            t = 10.0 ** ceil(log10(builtins.max(0, *tmp_val) + 1))
            new_max = builtins.max(DEFAULT_MAX, t) - 1
        else:
            new_max = cast("float", max)

        return new_min, new_max

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        d = super().options.copy()
        d.update({"min": self.min, "max": self.max, "step": self.step})
        return d

    @ValueWidget.value.setter  # type: ignore
    def value(self, value):
        """Set widget value, will raise Value error if not within min/max."""
        if not (self.min <= float(value) <= self.max):
            raise ValueError(
                f"value {value} is outside of the allowed range: "
                f"({self.min}, {self.max})"
            )
        ValueWidget.value.fset(self, value)  # type: ignore

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
    def step(self) -> Union[float, None]:
        """Step size for widget values (None if adaptive step is turned on)."""
        if self._widget._mgui_get_adaptive_step():
            return None
        return self._widget._mgui_get_step()

    @step.setter
    def step(self, value: Union[float, None]):
        if value is None:
            self._widget._mgui_set_adaptive_step(True)
        else:
            self._widget._mgui_set_adaptive_step(False)
            self._widget._mgui_set_step(value)

    @property
    def adaptive_step(self):
        """Whether the step size is adaptive."""
        return self.step is None

    @adaptive_step.setter
    def adaptive_step(self, value: bool):
        if value:
            self.step = None
        else:
            self.step = self._widget._mgui_get_step()

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


class MultiValueRangedWidget(RangedWidget):
    """Widget with a constrained *iterable* value, like a tuple."""

    @ValueWidget.value.setter  # type: ignore
    def value(self, value: Tuple[float, ...]):
        """Set widget value, will raise Value error if not within min/max."""
        if not isinstance(value, Iterable):
            raise ValueError(
                f"value {value!r} is not iterable, and must be for a "
                "MultiValueRangedWidget"
            )

        value = tuple(value)
        for v in value:
            if not (self.min <= float(v) <= self.max):
                raise ValueError(
                    f"value {v} is outside of the allowed range: "
                    f"({self.min}, {self.max})"
                )
        ValueWidget.value.fset(self, value)  # type: ignore
