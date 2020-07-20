"""A CombBox subclass that emits data objects when the index changes."""
from qtpy.QtCore import Signal
from qtpy.QtWidgets import QComboBox


class QDataComboBox(QComboBox):
    """A CombBox subclass that emits data objects when the index changes."""

    currentDataChanged = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.currentIndexChanged.connect(self._emit_data)

    def _emit_data(self, index: int) -> None:
        data = self.itemData(index)
        if data is not None:
            self.currentDataChanged.emit(data)
