"""A Slider with a natural logarithmic scale."""
import numpy as np
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSlider


class QLogSlider(QSlider):
    """A Slider Widget with a natural logarithmic scale."""

    PRECISION = 1000

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent=parent)
        self.setMaximum(10)

    def value(self):
        """Get the natural log slider value as a float."""
        return np.log(super().value() / self.PRECISION)

    def setValue(self, value):
        """Set integer slier position from float ``value``."""
        super().setValue(np.exp(value) * self.PRECISION)

    def setMaximum(self, value):
        """Set maximum position of slider in float units."""
        super().setMaximum(np.exp(value) * self.PRECISION)
