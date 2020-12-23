"""Widget implementations (adaptors) for the Qt backend."""
from typing import Any, Iterable, Optional, Tuple, Union

import qtpy
from qtpy import QtWidgets as QtW
from qtpy.QtCore import QEvent, QObject, Qt, QTimer, Signal
from qtpy.QtGui import QFont, QFontMetrics

from magicgui.types import FileDialogMode
from magicgui.widgets import _protocols
from magicgui.widgets._bases import Widget


class EventFilter(QObject):
    parentChanged = Signal()
    valueChanged = Signal(object)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ParentChange:
            # FIXME: error prone... but we need this to emit AFTER the event is handled
            def _try_emit():
                try:
                    self.parentChanged.emit()
                except AttributeError:
                    pass

            QTimer().singleShot(0, _try_emit)
        return False


class QBaseWidget(_protocols.WidgetProtocol):
    """Implements show/hide/native."""

    _qwidget: QtW.QWidget

    def __init__(self, qwidg: QtW.QWidget):
        self._qwidget = qwidg()
        self._event_filter = EventFilter()
        self._qwidget.installEventFilter(self._event_filter)

    def _mgui_show_widget(self):
        self._qwidget.show()

    def _mgui_hide_widget(self):
        self._qwidget.hide()

    def _mgui_get_enabled(self) -> bool:
        return self._qwidget.isEnabled()

    def _mgui_set_enabled(self, enabled: bool):
        self._qwidget.setEnabled(enabled)

    # TODO: this used to return _magic_widget ... figure out what we should be returning
    def _mgui_get_parent(self):
        return self._qwidget.parent()

    def _mgui_set_parent(self, widget: Widget):
        self._qwidget.setParent(widget.native)

    def _mgui_get_native_widget(self) -> QtW.QWidget:
        return self._qwidget

    def _mgui_get_width(self) -> int:
        """Return the current width of the widget."""
        return self._qwidget.width()

    def _mgui_set_min_width(self, value) -> None:
        """Set the minimum allowable width of the widget."""
        self._qwidget.setMinimumWidth(value)
        self._qwidget.resize(self._qwidget.sizeHint())

    def _mgui_bind_parent_change_callback(self, callback):
        self._event_filter.parentChanged.connect(callback)

    def _mgui_render(self):
        try:
            import numpy as np
        except ImportError:
            raise ModuleNotFoundError(
                "could not find module 'numpy'. "
                "Please `pip install numpy` to render widgets."
            ) from None

        img = self._qwidget.grab().toImage()
        bits = img.constBits()
        h, w, c = img.height(), img.width(), 4
        if qtpy.API_NAME == "PySide2":
            arr = np.array(bits).reshape(h, w, c)
        else:
            bits.setsize(h * w * c)
            arr = np.frombuffer(bits, np.uint8).reshape(h, w, c)

        return arr[:, :, [2, 1, 0, 3]]


class QBaseValueWidget(QBaseWidget, _protocols.ValueWidgetProtocol):
    """Implements get/set/bind_change."""

    def __init__(self, qwidg: QtW.QWidget, getter: str, setter: str, onchange: str):
        super().__init__(qwidg)
        self._getter_name = getter
        self._setter_name = setter
        self._onchange_name = onchange

    def _mgui_get_value(self) -> Any:
        return getattr(self._qwidget, self._getter_name)()

    def _mgui_set_value(self, value) -> None:
        getattr(self._qwidget, self._setter_name)(value)

    def _mgui_bind_change_callback(self, callback):
        signal_instance = getattr(self._qwidget, self._onchange_name, None)
        if signal_instance:
            signal_instance.connect(callback)


# STRING WIDGETS


class QBaseStringWidget(QBaseValueWidget):
    _qwidget: Union[QtW.QLineEdit, QtW.QTextEdit]

    def _mgui_set_value(self, value) -> None:
        super()._mgui_set_value(str(value))


class Label(QBaseStringWidget):
    # (can be both string or pixmap)
    def __init__(self):
        super().__init__(QtW.QLabel, "text", "setText", "")
        self._qwidget.setSizePolicy(QtW.QSizePolicy.Fixed, QtW.QSizePolicy.Fixed)

    def _mgui_bind_change_callback(self, callback):
        # raise NotImplementedError("QLabel has no change signal")
        pass

    def _mgui_set_value(self, value) -> None:
        # TODO: provide support for images as np.arrays
        super()._mgui_set_value(str(value))


class LineEdit(QBaseStringWidget):
    def __init__(self):
        super().__init__(QtW.QLineEdit, "text", "setText", "textChanged")


class TextEdit(QBaseStringWidget):
    def __init__(self):
        super().__init__(QtW.QTextEdit, "toPlainText", "setText", "textChanged")


# NUMBERS


class QBaseRangedWidget(QBaseValueWidget, _protocols.RangedWidgetProtocol):
    """Provides min/max/step implementations."""

    _qwidget: Union[QtW.QDoubleSpinBox, QtW.QSpinBox, QtW.QSlider]

    def __init__(self, qwidg):
        super().__init__(qwidg, "value", "setValue", "valueChanged")

    def _mgui_get_min(self) -> float:
        """Get the minimum possible value."""
        return self._qwidget.minimum()

    def _mgui_set_min(self, value: float):
        """Set the minimum possible value."""
        self._qwidget.setMinimum(value)

    def _mgui_get_max(self) -> float:
        """Set the maximum possible value."""
        return self._qwidget.maximum()

    def _mgui_set_max(self, value: float):
        """Set the maximum possible value."""
        self._qwidget.setMaximum(value)

    def _mgui_get_step(self) -> float:
        """Get the step size."""
        return self._qwidget.singleStep()

    def _mgui_set_step(self, value: float):
        """Set the step size."""
        self._qwidget.setSingleStep(value)


# BUTTONS


class QBaseButtonWidget(QBaseValueWidget, _protocols.SupportsText):
    _qwidget: Union[QtW.QCheckBox, QtW.QPushButton, QtW.QRadioButton, QtW.QToolButton]

    def __init__(self, qwidg):
        super().__init__(qwidg, "isChecked", "setChecked", "toggled")

    def _mgui_set_text(self, value: str) -> None:
        """Set text."""
        self._qwidget.setText(str(value))

    def _mgui_get_text(self) -> str:
        """Get text."""
        return self._qwidget.text()


class PushButton(QBaseButtonWidget):
    def __init__(self):
        QBaseValueWidget.__init__(
            self, QtW.QPushButton, "isChecked", "setChecked", "clicked"
        )


class CheckBox(QBaseButtonWidget):
    def __init__(self):
        super().__init__(QtW.QCheckBox)


class RadioButton(QBaseButtonWidget):
    def __init__(self):
        super().__init__(QtW.QRadioButton)


# class ToolButton(QBaseButtonWidget):
#     def __init__(self):
#         super().__init__(QtW.QToolButton)


# CATEGORICAL


class Container(
    QBaseWidget, _protocols.ContainerProtocol, _protocols.SupportsOrientation
):
    def __init__(self, orientation="vertical"):
        QBaseWidget.__init__(self, QtW.QWidget)
        if orientation == "horizontal":
            self._layout: QtW.QLayout = QtW.QHBoxLayout()
        else:
            self._layout = QtW.QVBoxLayout()
        self._qwidget.setLayout(self._layout)

    def _mgui_get_margins(self) -> Tuple[int, int, int, int]:
        return self._layout.contentsMargins()

    def _mgui_set_margins(self, margins: Tuple[int, int, int, int]) -> None:
        self._layout.setContentsMargins(*margins)

    def _mgui_add_widget(self, widget: Widget):
        _widget = widget.native
        self._layout.addWidget(_widget)

    def _mgui_insert_widget(self, position: int, widget: Widget):
        _widget = widget.native
        if position < 0:
            position = self._mgui_count() + position + 1

        self._layout.insertWidget(position, _widget)

    def _mgui_remove_widget(self, widget: Widget):
        self._layout.removeWidget(widget.native)
        widget.native.setParent(None)

    def _mgui_remove_index(self, position: int):
        # TODO: normalize position in superclass
        if position < 0:
            position = self._mgui_count() + position + 1
        item = self._layout.takeAt(position)
        item.widget().setParent(None)

    def _mgui_count(self) -> int:
        return self._layout.count()

    def _mgui_index(self, widget: Widget) -> int:
        return self._layout.indexOf(widget.native)

    def _mgui_get_index(self, index: int) -> Optional[Widget]:
        # We need to return a magicgui.Widget object, so this currently
        # requires storing the original object as a hidden attribute.
        # better way?
        item = self._layout.itemAt(index)
        if item:
            return item.widget()._magic_widget
        return None

    def _mgui_set_orientation(self, value) -> None:
        """Set orientation, value will be 'horizontal' or 'vertical'"""
        raise NotImplementedError(
            "Sorry, changing orientation after instantiation "
            "is not yet implemented for Qt."
        )

    def _mgui_get_orientation(self) -> str:
        """Set orientation, return either 'horizontal' or 'vertical'"""
        if isinstance(self, QtW.QHBoxLayout):
            return "horizontal"
        else:
            return "vertical"

    def _mgui_get_native_layout(self) -> QtW.QLayout:
        return self._layout


class SpinBox(QBaseRangedWidget):
    def __init__(self):
        super().__init__(QtW.QSpinBox)

    def _mgui_set_value(self, value) -> None:
        super()._mgui_set_value(int(value))


class FloatSpinBox(QBaseRangedWidget):
    def __init__(self):
        super().__init__(QtW.QDoubleSpinBox)

    def _mgui_set_value(self, value) -> None:
        super()._mgui_set_value(float(value))


class Slider(QBaseRangedWidget, _protocols.SupportsOrientation):
    _qwidget: QtW.QSlider

    def __init__(self):
        super().__init__(QtW.QSlider)
        self._mgui_set_orientation("horizontal")

    def _mgui_set_orientation(self, value) -> Any:
        """Get current value of the widget."""
        orientation = Qt.Vertical if value == "vertical" else Qt.Horizontal
        self._qwidget.setOrientation(orientation)

    def _mgui_get_orientation(self) -> Any:
        """Get current value of the widget."""
        orientation = self._qwidget.orientation()
        return "vertical" if orientation == Qt.Vertical else "horizontal"


class ComboBox(QBaseValueWidget, _protocols.CategoricalWidgetProtocol):
    _qwidget: QtW.QComboBox

    def __init__(self):
        super().__init__(QtW.QComboBox, "isChecked", "setCurrentIndex", "")
        self._qwidget.currentIndexChanged.connect(self._emit_data)

    def _emit_data(self, index: int):
        data = self._qwidget.itemData(index)
        if data is not None:
            self._event_filter.valueChanged.emit(data)

    def _mgui_bind_change_callback(self, callback):
        self._event_filter.valueChanged.connect(callback)

    def _mgui_get_value(self) -> Any:
        return self._qwidget.itemData(self._qwidget.currentIndex())

    def _mgui_set_value(self, value) -> None:
        self._qwidget.setCurrentIndex(self._qwidget.findData(value))

    def _mgui_set_choices(self, choices: Iterable[Tuple[str, Any]]) -> None:
        """Set current items in categorical type ``widget`` to ``choices``."""
        # FIXME: still not clearing all old choices correctly.
        if not list(choices):
            self._qwidget.clear()
            return

        names = {x[0] for x in choices}
        for i in range(self._qwidget.count()):
            if self._qwidget.itemText(i) not in names:
                self._qwidget.removeItem(i)
        for name, data in choices:
            if self._qwidget.findText(name) == -1:
                self._qwidget.addItem(name, data)
        current = self._mgui_get_value()
        if current not in {x[1] for x in choices}:
            first = next(iter(choices))[1]
            self._qwidget.setCurrentIndex(self._qwidget.findData(first))
            self._qwidget.removeItem(self._qwidget.findData(current))

    def _mgui_get_choices(self) -> Tuple[Tuple[str, Any]]:
        """Show the widget."""
        return tuple(  # type: ignore
            (self._qwidget.itemText(i), self._qwidget.itemData(i))
            for i in range(self._qwidget.count())
        )


class DateTimeEdit(QBaseValueWidget):
    def __init__(self):
        super().__init__(QtW.QDateTimeEdit, "", "setDateTime", "dateTimeChanged")

    def _mgui_get_value(self):
        try:
            return self._qwidget.dateTime().toPython()
        except TypeError:
            return self._qwidget.dateTime().toPyDateTime()


QFILE_DIALOG_MODES = {
    FileDialogMode.EXISTING_FILE: QtW.QFileDialog.getOpenFileName,
    FileDialogMode.EXISTING_FILES: QtW.QFileDialog.getOpenFileNames,
    FileDialogMode.OPTIONAL_FILE: QtW.QFileDialog.getSaveFileName,
    FileDialogMode.EXISTING_DIRECTORY: QtW.QFileDialog.getExistingDirectory,
}


def show_file_dialog(
    mode: Union[str, FileDialogMode] = FileDialogMode.EXISTING_FILE,
    caption: str = None,
    start_path: str = None,
    filter: str = None,
    parent=None,
) -> Optional[str]:
    show_dialog = QFILE_DIALOG_MODES[FileDialogMode(mode)]
    args = (parent, caption, start_path, filter)
    if mode is FileDialogMode.EXISTING_DIRECTORY:
        result = show_dialog(*args)
    else:
        result, _ = show_dialog(*args)
    return result or None


def get_text_width(text) -> int:
    """Return the width required to render ``text``."""
    fm = QFontMetrics(QFont("", 0))
    return fm.boundingRect(text).width() + 5
