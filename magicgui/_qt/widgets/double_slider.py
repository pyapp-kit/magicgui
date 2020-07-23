"""A Slider that can handle float values."""
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QSlider


class QDoubleSlider(QSlider):
    """A Slider Widget that can handle float values."""

    PRECISION = 1000

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent=parent)
        self.setMaximum(10)

    def value(self):
        """Get the slider value and convert to float."""
        return super().value() / self.PRECISION

    def setValue(self, value: float):
        """Set integer slider position from float ``value``."""
        super().setValue(value * self.PRECISION)

    def setMaximum(self, value: float):
        """Set maximum position of slider in float units."""
        super().setMaximum(value * self.PRECISION)
