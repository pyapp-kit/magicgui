from magicgui.widgets import _protocols

from .mixins import _OrientationMixin
from .ranged_widget import RangedWidget


class SliderWidget(RangedWidget, _OrientationMixin):
    """Widget with a contstrained value and orientation. Wraps SliderWidgetProtocol.

    Parameters
    ----------
    orientation : str, {'horizontal', 'vertical'}
        The orientation for the slider, by default "horizontal"
    """

    _widget: _protocols.SliderWidgetProtocol

    def __init__(self, orientation: str = "horizontal", **kwargs):
        super().__init__(**kwargs)

        self.orientation = orientation

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        d = super().options.copy()
        d.update({"orientation": self.orientation})
        return d
