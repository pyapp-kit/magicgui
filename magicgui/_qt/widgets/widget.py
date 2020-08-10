"""Base Widget Type."""
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QWidget


class WidgetType(QWidget):
    """Widget that reports when its parent has changed."""

    parentChanged = Signal()

    def setParent(self, parent: QWidget):
        """Set parent widget and emit signal."""
        super().setParent(parent)
        self.parentChanged.emit()
