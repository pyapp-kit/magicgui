from __future__ import annotations

import builtins
from abc import ABC, abstractmethod
from math import ceil, log10
from typing import TYPE_CHECKING, Callable, Iterable, Tuple, TypeVar, Union, cast

from magicgui.types import Undefined, _Undefined

from ._value_widget import ValueWidget

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from magicgui.widgets import protocols

    from ._widget import WidgetKwargs

T = TypeVar("T", int, float, Tuple[Union[int, float], ...])
DEFAULT_MIN = 0.0
DEFAULT_MAX = 1000.0


class RangedWidget(ValueWidget[T]):
    """Widget with a constrained value. Wraps RangedWidgetProtocol.

    Parameters
    ----------
    value : Any, optional
        The starting value for the widget.
    min : float, optional
        The minimum allowable value, by default 0 (or `value` if `value` is less than 0)
    max : float, optional
        The maximum allowable value, by default 999 (or `value` if `value` is greater
        than 999)
    step : float, optional
        The step size for incrementing the value, by default adaptive step is used
    bind : Callable[[ValueWidget], Any] | Any, optional
        A value or callback to bind this widget. If provided, whenever
        [`widget.value`][magicgui.widgets.bases.ValueWidget.value] is
        accessed, the value provided here will be returned instead. `bind` may be a
        callable, in which case `bind(self)` will be returned (i.e. your bound callback
        must accept a single parameter, which is this widget instance).
    nullable : bool, optional
        If `True`, the widget will accepts `None` as a valid value, by default `False`.
    **base_widget_kwargs : Any
        All additional keyword arguments are passed to the base
        [`magicgui.widgets.Widget`][magicgui.widgets.Widget] constructor.
    """

    _widget: protocols.RangedWidgetProtocol

    def __init__(
        self,
        value: T | _Undefined = Undefined,
        *,
        min: float | _Undefined = Undefined,
        max: float | _Undefined = Undefined,
        step: float | _Undefined | None = Undefined,
        bind: T | Callable[[ValueWidget], T] | _Undefined = Undefined,
        nullable: bool = False,
        **base_widget_kwargs: Unpack[WidgetKwargs],
    ) -> None:
        # value should be set *after* min max is set
        super().__init__(
            bind=bind,  # type: ignore
            nullable=nullable,
            **base_widget_kwargs,
        )

        if step is Undefined or step is None:
            self.step = None
            self._widget._mgui_set_step(1)
        else:
            self.step = cast(float, step)

        self.min, self.max = self._init_range(value, min, max)
        if value not in (Undefined, None):
            self.value = value

    def _init_range(
        self,
        value: T | _Undefined,
        min: float | _Undefined,
        max: float | _Undefined,
    ) -> tuple[float, float]:
        """Return min and max based on given value and arguments.

        If min or max are unset, constrain so the given value is within the range.
        """
        tmp_val: tuple[float | int, ...]
        if value is None or isinstance(value, _Undefined):
            tmp_val = (1,)
        elif isinstance(value, (tuple, list)):
            tmp_val = tuple(1 if v is None else float(v) for v in value)
        else:
            tmp_val = (float(value),)

        new_min: float = (
            cast("float", min)
            if min is not Undefined
            else builtins.min(DEFAULT_MIN, *tmp_val)
        )

        if max is Undefined:
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
    def value(self, value: T) -> None:
        """Set widget value, will raise Value error if not within min/max."""
        val: tuple[float, ...] = value if isinstance(value, tuple) else (value,)
        if any(float(v) < self.min or float(v) > self.max for v in val):
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
    def min(self, value: float) -> None:
        self._widget._mgui_set_min(value)

    @property
    def max(self) -> float:
        """Maximum allowable value for the widget."""
        return self._widget._mgui_get_max()

    @max.setter
    def max(self, value: float) -> None:
        self._widget._mgui_set_max(value)

    @property
    def step(self) -> float | None:
        """Step size for widget values (None if adaptive step is turned on)."""
        if self._widget._mgui_get_adaptive_step():
            return None
        return self._widget._mgui_get_step()

    @step.setter
    def step(self, value: float | None) -> None:
        if value is None:
            self._widget._mgui_set_adaptive_step(True)
        else:
            self._widget._mgui_set_adaptive_step(False)
            self._widget._mgui_set_step(value)

    @property
    def adaptive_step(self) -> bool:
        """Whether the step size is adaptive.

        Adaptive decimal step means that the step size will continuously be adjusted to
        one power of ten below the current value. So when the value is 1100, the step is
        set to 100, so stepping up once increases it to 1200. For 1200 stepping up takes
        it to 1300. For negative values, stepping down from -1100 goes to -1200.
        """
        return self.step is None

    @adaptive_step.setter
    def adaptive_step(self, value: bool) -> None:
        self.step = None if value else self._widget._mgui_get_step()

    @property
    def range(self) -> tuple[float, float]:
        """Range of allowable values for the widget."""
        return self.min, self.max

    @range.setter
    def range(self, value: tuple[float, float]) -> None:
        self.min, self.max = value


class TransformedRangedWidget(RangedWidget[float], ABC):
    """Widget with a constrained value. Wraps RangedWidgetProtocol.

    This can be used to map one domain of numbers onto another, useful for creating
    things like LogSliders.  Subclasses must reimplement ``_value_from_position`` and
    ``_position_from_value``.

    Parameters
    ----------
    value : Any, optional
        The starting value for the widget.
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
    bind : Callable[[ValueWidget], Any] | Any, optional
        A value or callback to bind this widget. If provided, whenever
        [`widget.value`][magicgui.widgets.bases.ValueWidget.value] is
        accessed, the value provided here will be returned instead. `bind` may be a
        callable, in which case `bind(self)` will be returned (i.e. your bound callback
        must accept a single parameter, which is this widget instance).
    nullable : bool, optional
        If `True`, the widget will accepts `None` as a valid value, by default `False`.
    **base_widget_kwargs : Any
        All additional keyword arguments are passed to the base
        [`magicgui.widgets.Widget`][magicgui.widgets.Widget] constructor.
    """

    _widget: protocols.RangedWidgetProtocol

    def __init__(
        self,
        value: T | _Undefined = Undefined,
        *,
        min: float = 0,
        max: float = 100,
        min_pos: int = 0,
        max_pos: int = 100,
        step: int = 1,
        bind: T | Callable[[ValueWidget], T] | _Undefined = Undefined,
        nullable: bool = False,
        **base_widget_kwargs: Unpack[WidgetKwargs],
    ) -> None:
        self._min = min
        self._max = max
        self._min_pos = min_pos
        self._max_pos = max_pos
        ValueWidget.__init__(  # type: ignore
            self, value=value, bind=bind, nullable=nullable, **base_widget_kwargs
        )

        self._widget._mgui_set_min(self._min_pos)
        self._widget._mgui_set_max(self._max_pos)
        self._widget._mgui_set_step(step)

    # Just a linear scaling example.
    # Replace _value_from_position, and _position_from_value in subclasses
    # to implement more complex value->position lookups
    @property
    def _scale(self) -> float:
        """Slope of a linear map.  Just used as an example."""
        return (self.max - self.min) / (self._max_pos - self._min_pos)

    @abstractmethod
    def _value_from_position(self, position: float) -> float:
        """Return 'real' value given internal widget position."""
        return self.min + self._scale * (position - self._min_pos)

    @abstractmethod
    def _position_from_value(self, value: float) -> float:
        """Return internal widget position given 'real' value."""
        return (value - self.min) / self._scale + self._min_pos

    #########

    @property
    def value(self) -> float:
        """Return current value of the widget."""
        return self._value_from_position(self._widget._mgui_get_value())

    @value.setter
    def value(self, value: float) -> None:
        return self._widget._mgui_set_value(self._position_from_value(value))

    @property
    def min(self) -> float:
        """Minimum allowable value for the widget."""
        return self._min

    @min.setter
    def min(self, value: float) -> None:
        prev = self.value
        self._min = value
        self.value = prev

    @property
    def max(self) -> float:
        """Maximum allowable value for the widget."""
        return self._max

    @max.setter
    def max(self, value: float) -> None:
        prev = self.value
        self._max = value
        self.value = prev


class MultiValueRangedWidget(RangedWidget[T]):
    """Widget with a constrained *iterable* value, like a tuple."""

    @ValueWidget.value.setter  # type: ignore
    def value(self, value: tuple[float, ...]) -> None:
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
