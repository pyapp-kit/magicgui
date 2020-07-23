"""A Slider with a natural logarithmic scale."""
import math

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSlider


class QLogSlider(QSlider):
    """A Slider Widget with a natural logarithmic scale."""

    PRECISION = 1000

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent=parent)
        self.setMinimum(0)
        self.setMaximum(10)

    def value(self):
        """Get the natural log slider value as a float."""
        return math.log(super().value() / self.PRECISION)

    def setValue(self, value):
        """Set integer slier position from float ``value``."""
        super().setValue(int(math.exp(value) * self.PRECISION))

    def setMinimum(self, value):
        """Set minimum position of slider in float units."""
        super().setMinimum(math.exp(value) * self.PRECISION)

    def setMaximum(self, value):
        """Set maximum position of slider in float units."""
        super().setMaximum(int(math.exp(value) * self.PRECISION))
