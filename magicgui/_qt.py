import sys
from contextlib import contextmanager
from enum import Enum, EnumMeta
from typing import Any, Callable, Dict, Iterable, NamedTuple, Optional, Type, Tuple

from qtpy.QtCore import Signal, SignalInstance
from qtpy.QtWidgets import (
    QAbstractButton,
    QAbstractSlider,
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


@contextmanager
def event_loop():
    """Start a Qt event loop in which to run the application."""
    app = QApplication.instance() or QApplication(sys.argv)
    yield
    app.exec_()


WidgetType = QWidget
ButtonType = QPushButton
SignalType = Signal


class GetSetOnChange(NamedTuple):
    getter: Callable[[], Any]
    setter: Callable[[Any], None]
    onchange: SignalInstance


class Layout(Enum):
    vertical = QVBoxLayout
    horizontal = QHBoxLayout
    grid = QGridLayout
    form = QFormLayout

    @classmethod
    def _missing_(cls, value: object) -> Any:
        options = cls._member_names_
        raise ValueError(f"'{value}' is not a valid Layout. Options include: {options}")


class QDataComboBox(QComboBox):
    currentDataChanged = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.currentIndexChanged.connect(self._emit_data)

    def _emit_data(self, index: int) -> None:
        data = self.itemData(index)
        if data is not None:
            self.currentDataChanged.emit(data)


def type2widget(type_: type) -> Type[WidgetType]:
    simple: Dict[type, Type[WidgetType]] = {
        bool: QCheckBox,
        int: QSpinBox,
        float: QDoubleSpinBox,
        str: QLineEdit,
        type(None): QLineEdit,
    }
    if type_ in simple:
        return simple[type_]
    elif isinstance(type_, EnumMeta):
        return QDataComboBox


def getter_setter_onchange(widget: WidgetType) -> GetSetOnChange:
    if isinstance(widget, QComboBox):

        def getter():
            return widget.itemData(widget.currentIndex())

        onchange = (
            widget.currentDataChanged
            if isinstance(widget, QDataComboBox)
            else widget.currentIndexChanged
        )
        return GetSetOnChange(getter, widget.setCurrentIndex, onchange)
    elif isinstance(widget, QStatusBar):
        return GetSetOnChange(
            widget.currentMessage, widget.showMessage, widget.messageChanged
        )
    elif isinstance(widget, QLineEdit):
        return GetSetOnChange(widget.text, widget.setText, widget.textChanged)
    elif isinstance(widget, (QAbstractButton, QGroupBox)):
        return GetSetOnChange(widget.isChecked, widget.setChecked, widget.toggled)
    elif isinstance(widget, QDateTimeEdit):
        return GetSetOnChange(
            widget.dateTime, widget.setDateTime, widget.dateTimeChanged
        )
    elif isinstance(widget, (QAbstractSpinBox, QAbstractSlider)):
        return GetSetOnChange(widget.value, widget.setValue, widget.valueChanged)
    elif isinstance(widget, QTabWidget):
        return GetSetOnChange(
            widget.currentIndex, widget.setCurrentIndex, widget.currentChanged
        )
    elif isinstance(widget, QSplitter):
        return GetSetOnChange(widget.sizes, widget.setSizes, widget.splitterMoved)
    raise ValueError(f"Unrecognized widget Type: {widget}")


def set_categorical_choices(widget: WidgetType, choices: Iterable[Tuple[str, Any]]):
    names = [x[0] for x in choices]
    for i in range(widget.count()):
        if widget.itemText(i) not in names:
            widget.removeItem(i)
    for name, data in choices:
        if widget.findText(name) == -1:
            widget.addItem(name, data)


def get_categorical_widget():
    return QDataComboBox


def is_categorical(widget: WidgetType):
    return isinstance(widget, QComboBox)


def get_categorical_index(widget: WidgetType, value: Any):
    return next(i for i in range(widget.count()) if widget.itemData(i) == value)


def make_widget(
    WidgetType: Type[WidgetType],
    name: Optional[str] = None,
    parent: WidgetType = None,
    **kwargs,
) -> WidgetType:
    widget = WidgetType(parent=parent)
    if name:
        widget.setObjectName(name)
    for key, val in kwargs.items():
        setter = getattr(widget, f"set{key[0].upper() + key[1:]}", None)
        if setter:
            setter(val)

    return widget
