from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Tuple, Union

from magicgui.types import Undefined, _Undefined

from ._mixins import _OrientationMixin
from ._ranged_widget import MultiValueRangedWidget, RangedWidget, T

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from magicgui.widgets import protocols

    from ._widget import WidgetKwargs


class SliderWidget(RangedWidget[T], _OrientationMixin):
    """Widget with a constrained value and orientation. Wraps SliderWidgetProtocol.

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
    orientation : str, {'horizontal', 'vertical'}
        The orientation for the slider, by default "horizontal"
    readout : bool, optional
        Whether to show the editable spinbox next to the slider
    tracking : bool, optional
        If tracking is enabled (the default), the slider emits the `changed`
        signal while the slider is being dragged. If tracking is disabled,
        the slider emits the `changed` signal only after the user releases
        the slider.
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

    _widget: protocols.SliderWidgetProtocol

    def __init__(
        self,
        value: T | _Undefined = Undefined,
        *,
        min: float | _Undefined = Undefined,
        max: float | _Undefined = Undefined,
        step: float | _Undefined | None = Undefined,
        orientation: str = "horizontal",
        readout: bool = True,
        tracking: bool = True,
        bind: T | Callable[[protocols.ValueWidgetProtocol], T] | _Undefined = Undefined,
        nullable: bool = False,
        **base_widget_kwargs: Unpack[WidgetKwargs],
    ) -> None:
        base_widget_kwargs["backend_kwargs"] = {
            "readout": readout,
            "orientation": orientation,
        }
        super().__init__(
            value=value,  # type: ignore
            min=min,
            max=max,
            step=step,
            bind=bind,  # type: ignore
            nullable=nullable,
            **base_widget_kwargs,
        )
        self.readout = readout
        self.tracking = tracking

    @property
    def tracking(self) -> bool:
        """Return whether slider tracking is enabled.

        If tracking is enabled (the default), the slider emits the changed()
        signal while the slider is being dragged. If tracking is disabled,
        the slider emits the changed() signal only when the user releases
        the slider.
        """
        return self._widget._mgui_get_tracking()

    @tracking.setter
    def tracking(self, value: bool) -> None:
        """Set whether slider tracking is enabled."""
        self._widget._mgui_set_tracking(value)

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        d = super().options.copy()
        d.update({"orientation": self.orientation, "readout": self._readout})
        return d

    @property
    def readout(self) -> bool:
        """Get visibility state of readout widget."""
        return self._readout

    @readout.setter
    def readout(self, value: bool) -> None:
        """Set visibility state of readout widget."""
        self._readout = value
        self._widget._mgui_set_readout_visibility(value)


class MultiValuedSliderWidget(
    MultiValueRangedWidget[Tuple[Union[int, float], ...]], SliderWidget
):
    """Slider widget that expects a iterable value."""

    _widget: protocols.SliderWidgetProtocol
