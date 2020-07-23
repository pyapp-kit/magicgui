"""A Slider with a natural logarithmic scale."""
import math

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSlider


class QLogSlider(QSlider):
    """A Slider Widget with a natural logarithmic scale."""

    PRECISION = 1000

    def __init__(self, parent=None, *, base=math.e):
        super().__init__(Qt.Horizontal, parent=parent)
        self.base = base
        self.setMinimum(0)
        self.setMaximum(10)

    def value(self):
        """Get the natural log slider value as a float."""
        return math.log(super().value() / self.PRECISION, self.base)

    def setValue(self, value: float):
        """Set integer slier position from float ``value``."""
        super().setValue(int(math.pow(self.base, value) * self.PRECISION))

    def setMinimum(self, value: float):
        """Set minimum position of slider in float units."""
        super().setMinimum(int(math.pow(self.base, value) * self.PRECISION))

    def setMaximum(self, value: float):
        """Set maximum position of slider in float units."""
        super().setMaximum(int(math.pow(self.base, value) * self.PRECISION))
