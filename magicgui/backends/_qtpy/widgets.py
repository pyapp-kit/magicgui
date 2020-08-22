"""Widget implementations (adaptors) for the Qt backend."""
from typing import Any, Iterable, Optional, Tuple, Union

from qtpy import QtWidgets as QtW
from qtpy.QtCore import QEvent, QObject, Qt, QTimer, Signal

from magicgui import protocols
from magicgui.widgets import FileDialogMode, Widget


class EventFilter(QObject):
    parentChanged = Signal()
    valueChanged = Signal(object)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ParentChange:
            # FIXME: error prone... but we need this to emit AFTER the event is handled
            QTimer().singleShot(1, self.parentChanged.emit)
        return False


class QBaseWidget(protocols.WidgetProtocol):
    """Implements show/hide/native."""

    _qwidget: QtW.QWidget

    def __init__(self, qwidg: QtW.QWidget):
        self._qwidget = qwidg()
        self._event_filter = EventFilter()
        self._qwidget.installEventFilter(self._event_filter)

    def _mg_show_widget(self):
        self._qwidget.show()

    def _mg_hide_widget(self):
        self._qwidget.hide()

    def _mg_get_enabled(self) -> bool:
        return self._qwidget.isEnabled()

    def _mg_set_enabled(self, enabled: bool):
        self._qwidget.setEnabled(enabled)

    # TODO: this used to return _magic_widget ... figure out what we should be returning
    def _mg_get_parent(self):
        return self._qwidget.parent()

    def _mg_set_parent(self, widget: Widget):
        self._qwidget.setParent(widget.native)

    def _mg_get_native_widget(self) -> QtW.QWidget:
        return self._qwidget

    def _mg_bind_parent_change_callback(self, callback):
        self._event_filter.parentChanged.connect(callback)


class QBaseValueWidget(QBaseWidget, protocols.ValueWidgetProtocol):
    """Implements get/set/bind_change."""

    def __init__(
        self, qwidg: QtW.QWidget, getter: str, setter: str, onchange: str,
    ):
        super().__init__(qwidg)
        self._getter_name = getter
        self._setter_name = setter
        self._onchange_name = onchange

    def _mg_get_value(self) -> Any:
        return getattr(self._qwidget, self._getter_name)()

    def _mg_set_value(self, value) -> None:
        getattr(self._qwidget, self._setter_name)(value)

    def _mg_bind_change_callback(self, callback):
        signal_instance = getattr(self._qwidget, self._onchange_name, None)
        if signal_instance:
            signal_instance.connect(callback)


# STRING WIDGETS


class QBaseStringWidget(QBaseValueWidget):
    _qwidget: Union[QtW.QLineEdit, QtW.QTextEdit]

    def _mg_set_value(self, value) -> None:
        super()._mg_set_value(str(value))


class Label(QBaseStringWidget):
    # (can be both string or pixmap)
    def __init__(self):
        super().__init__(QtW.QLabel, "text", "setText", "")

    def _mg_bind_change_callback(self, callback):
        # raise NotImplementedError("QLabel has no change signal")
        pass

    def _mg_set_value(self, value) -> None:
        # TODO: provide support for images as np.arrays
        super()._mg_set_value(str(value))


class LineEdit(QBaseStringWidget):
    def __init__(self):
        super().__init__(QtW.QLineEdit, "text", "setText", "textChanged")


class TextEdit(QBaseStringWidget):
    def __init__(self):
        super().__init__(QtW.QTextEdit, "toPlainText", "setText", "textChanged")


# NUMBERS


class QBaseRangedWidget(QBaseValueWidget, protocols.RangedWidgetProtocol):
    """Provides min/max/step implementations."""

    _qwidget: Union[QtW.QDoubleSpinBox, QtW.QSpinBox, QtW.QSlider]

    def __init__(self, qwidg):
        super().__init__(qwidg, "value", "setValue", "valueChanged")

    def _mg_get_minimum(self) -> float:
        """Get the minimum possible value."""
        return self._qwidget.minimum()

    def _mg_set_minimum(self, value: float):
        """Set the minimum possible value."""
        self._qwidget.setMinimum(value)

    def _mg_get_maximum(self) -> float:
        """Set the maximum possible value."""
        return self._qwidget.maximum()

    def _mg_set_maximum(self, value: float):
        """Set the maximum possible value."""
        self._qwidget.setMaximum(value)

    def _mg_get_step(self) -> float:
        """Get the step size."""
        return self._qwidget.singleStep()

    def _mg_set_step(self, value: float):
        """Set the step size."""
        self._qwidget.setSingleStep(value)


# BUTTONS


class QBaseButtonWidget(QBaseValueWidget, protocols.SupportsText):
    _qwidget: Union[QtW.QCheckBox, QtW.QPushButton, QtW.QRadioButton, QtW.QToolButton]

    def __init__(self, qwidg):
        super().__init__(qwidg, "isChecked", "setChecked", "toggled")

    def _mg_set_text(self, value: str) -> None:
        """Set text."""
        self._qwidget.setText(str(value))

    def _mg_get_text(self) -> str:
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
    QBaseWidget, protocols.ContainerProtocol, protocols.SupportsOrientation
):
    def __init__(self, orientation="horizontal"):
        QBaseWidget.__init__(self, QtW.QWidget)
        if orientation == "horizontal":
            self._layout: QtW.QLayout = QtW.QHBoxLayout()
        else:
            self._layout = QtW.QFormLayout()
        self._qwidget.setLayout(self._layout)

    def _mg_add_widget(self, widget: Widget):
        label = widget.name
        _widget = widget.native
        if isinstance(self._layout, QtW.QFormLayout):
            self._layout.addRow(label, _widget)
        else:
            self._layout.addWidget(_widget)

    def _mg_insert_widget(self, position: int, widget: Widget):
        label = widget.name
        _widget = widget.native
        if position < 0:
            position = self._mg_count() + position + 1

        if isinstance(self._layout, QtW.QFormLayout):
            self._layout.insertRow(position, label, _widget)
        else:
            self._layout.insertWidget(position, _widget)

    def _mg_remove_widget(self, widget: Widget):
        if isinstance(self._layout, QtW.QFormLayout):
            self._layout.removeRow(widget.native)
        else:
            self._layout.removeWidget(widget.native)

    def _mg_remove_index(self, position: int):
        # TODO: normalize position in superclass
        if position < 0:
            position = self._mg_count() + position + 1
        if isinstance(self._layout, QtW.QFormLayout):
            self._layout.removeRow(position)
        else:
            self._layout.takeAt(position)

    def _mg_count(self) -> int:
        return self._layout.count()

    def _mg_index(self, widget: Widget) -> int:
        if isinstance(self._layout, QtW.QFormLayout):
            return self._layout.l.getWidgetPosition(widget.native)[0]
        else:
            return self._layout.indexOf(widget.native)

    def _mg_get_index(self, index: int) -> Optional[Widget]:
        # We need to return a magicgui.Widget object, so this currently
        # requires storing the original object as a hidden attribute.
        # better way?
        item = self._layout.itemAt(index)
        if item:
            return item.widget()._magic_widget
        return None

    def _mg_set_orientation(self, value) -> None:
        """Set orientation, value will be 'horizontal' or 'vertical'"""
        pass

    def _mg_get_orientation(self) -> str:
        """Set orientation, return either 'horizontal' or 'vertical'"""
        if isinstance(self, QtW.QHBoxLayout):
            return "horizontal"
        else:
            return "vertical"

    def _mg_get_native_layout(self) -> QtW.QLayout:
        return self._layout


class SpinBox(QBaseRangedWidget):
    def __init__(self):
        super().__init__(QtW.QSpinBox)

    def _mg_set_value(self, value) -> None:
        super()._mg_set_value(int(value))


class FloatSpinBox(QBaseRangedWidget):
    def __init__(self):
        super().__init__(QtW.QDoubleSpinBox)

    def _mg_set_value(self, value) -> None:
        super()._mg_set_value(float(value))


class Slider(QBaseRangedWidget, protocols.SupportsOrientation):
    _qwidget: QtW.QSlider

    def __init__(self):
        super().__init__(QtW.QSlider)
        self._mg_set_orientation("horizontal")

    def _mg_set_orientation(self, value) -> Any:
        """Get current value of the widget."""
        orientation = Qt.Vertical if value == "vertical" else Qt.Horizontal
        self._qwidget.setOrientation(orientation)

    def _mg_get_orientation(self) -> Any:
        """Get current value of the widget."""
        orientation = self._qwidget.orientation()
        return "vertical" if orientation == Qt.Vertical else "horizontal"


class ComboBox(QBaseValueWidget, protocols.CategoricalWidgetProtocol):
    _qwidget: QtW.QComboBox

    def __init__(self):
        super().__init__(QtW.QComboBox, "isChecked", "setCurrentIndex", "")
        self._qwidget.currentIndexChanged.connect(self._emit_data)

    def _emit_data(self, index: int):
        data = self._qwidget.itemData(index)
        if data is not None:
            self._event_filter.valueChanged.emit(data)

    def _mg_bind_change_callback(self, callback):
        self._event_filter.valueChanged.connect(callback)

    def _mg_get_value(self) -> Any:
        return self._qwidget.itemData(self._qwidget.currentIndex())

    def _mg_set_value(self, value) -> None:
        self._qwidget.setCurrentIndex(self._qwidget.findData(value))

    def _mg_set_choices(self, choices: Iterable[Tuple[str, Any]]) -> None:
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
        current = self._mg_get_value()
        if current not in {x[1] for x in choices}:
            first = next(iter(choices))[1]
            self._qwidget.setCurrentIndex(self._qwidget.findData(first))
            self._qwidget.removeItem(self._qwidget.findData(current))

    def _mg_get_choices(self) -> Tuple[Tuple[str, Any]]:
        """Show the widget."""
        return tuple(  # type: ignore
            (self._qwidget.itemText(i), self._qwidget.itemData(i))
            for i in range(self._qwidget.count())
        )


class DateTimeEdit(QBaseValueWidget):
    def __init__(self):
        super().__init__(QtW.QDateTimeEdit, "", "setDateTime", "dateTimeChanged")

    def _mg_get_value(self):
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
    parent=None,
) -> Optional[str]:
    show_dialog = QFILE_DIALOG_MODES[FileDialogMode(mode)]
    if mode is FileDialogMode.EXISTING_DIRECTORY:
        result = show_dialog(parent, caption, start_path)
    else:
        result, _ = show_dialog(parent, caption, start_path)
    return result or None
