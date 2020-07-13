"""Base Widget Type."""
from qtpy.QtWidgets import QWidget
from qtpy.QtCore import Signal


class WidgetType(QWidget):
    """Widget that reports when its parent has changed."""

    parentChanged = Signal()

    def setParent(self, parent):
        """Set parent widget and emit signal."""
        super().setParent(parent)
        self.parentChanged.emit()
