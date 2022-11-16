from magicgui.widgets import protocols

from ._mixins import _OrientationMixin
from ._ranged_widget import MultiValueRangedWidget, RangedWidget


class SliderWidget(RangedWidget, _OrientationMixin):
    """Widget with a contstrained value and orientation. Wraps SliderWidgetProtocol.

    Parameters
    ----------
    orientation : str, {'horizontal', 'vertical'}
        The orientation for the slider, by default "horizontal"
    readout : bool, optional
        Whether to show the editable spinbox next to the slider
    tracking : bool, optional
        If tracking is enabled (the default), the slider emits the `changed`
        signal while the slider is being dragged. If tracking is disabled,
        the slider emits the `changed` signal only after the user releases
        the slider.
    """

    _widget: protocols.SliderWidgetProtocol

    def __init__(
        self,
        orientation: str = "horizontal",
        readout: bool = True,
        tracking: bool = True,
        **kwargs
    ):
        kwargs["backend_kwargs"] = {"readout": readout, "orientation": orientation}
        super().__init__(**kwargs)
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
    def readout(self, value: bool):
        """Set visibility state of readout widget."""
        self._readout = value
        self._widget._mgui_set_readout_visibility(value)


class MultiValuedSliderWidget(MultiValueRangedWidget, SliderWidget):
    """Slider widget that expects a iterable value."""

    _widget: protocols.SliderWidgetProtocol
