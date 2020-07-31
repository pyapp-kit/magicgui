"""A CombBox subclass that emits data objects when the index changes."""
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QComboBox, QWidget


class QDataComboBox(QComboBox):
    """A CombBox subclass that emits data objects when the index changes."""

    currentDataChanged = Signal(object)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.currentIndexChanged.connect(self._emit_data)

    def _emit_data(self, index: int):
        data = self.itemData(index)
        if data is not None:
            self.currentDataChanged.emit(data)
