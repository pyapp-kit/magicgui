"""Widget implementations (adaptors) for the Qt backend."""
from typing import Any, Iterable, Protocol, Tuple, Union, Optional

from qtpy import QtWidgets as QtW
from qtpy.QtCore import QObject, Qt, Signal

from magicgui.base import (
    BaseLayout,
    BaseNumberWidget,
    BaseWidget,
    SupportsChoices,
    SupportsOrientation,
)
from magicgui.widget import Widget


class HasQWidget(Protocol):
    _qwidget: QtW.QWidget


class QBaseWidget(BaseWidget, HasQWidget):
    """Provides get/set/show/bind/native implementations."""

    def __init__(
        self,
        mg_widget: Widget,
        qwidg: QtW.QWidget,
        getter: str,
        setter: str,
        onchange: str,
    ):
        super().__init__(mg_widget)
        self._qwidget = qwidg()
        # store the magicgui.Widget instance on the QWidget
        # currently, this is only needed for Layout._mg_get_index
        # TODO: figure out if there is a way around that.
        self._qwidget._magic_widget = mg_widget
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

    def _mg_show_widget(self):
        self._qwidget.show()

    def _mg_hide_widget(self):
        self._qwidget.hide()

    def _mg_get_native_widget(self):
        return self._qwidget


class QSupportsOrientation(SupportsOrientation, HasQWidget):
    def _mg_set_orientation(self, value) -> Any:
        """Get current value of the widget."""
        orientation = Qt.Vertical if value == "vertical" else Qt.Horizontal
        self._qwidget.setOrientation(orientation)

    def _mg_get_orientation(self) -> Any:
        """Get current value of the widget."""
        orientation = self._qwidget.orientation()
        return "vertical" if orientation == Qt.Vertical else "horizontal"


# STRING WIDGETS

QStringWidget = Union[QtW.QLineEdit, QtW.QTextEdit]


class QBaseStringWidget(QBaseWidget):
    def __init__(self, mg_widget, qwidg: QStringWidget, *args):
        super().__init__(mg_widget, qwidg, *args)

    def _mg_set_value(self, value) -> None:
        super()._mg_set_value(str(value))


class LineEdit(QBaseStringWidget):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QLineEdit, "text", "setText", "textChanged")


class TextEdit(QBaseStringWidget):
    def __init__(self, mg_widget):
        super().__init__(
            mg_widget, QtW.QTextEdit, "toPlainText", "setText", "textChanged"
        )


# LABEL (can be both string or pixmap)


class Label(QBaseStringWidget):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QLabel, "text", "setText", "")

    def _mg_bind_change_callback(self, callback):
        raise NotImplementedError("QLabel has no change signal")

    def _mg_set_value(self, value) -> None:
        # TODO: provide support for images as np.arrays
        super()._mg_set_value(str(value))


# BUTTONS

QButtonWidget = Union[QtW.QCheckBox, QtW.QPushButton, QtW.QRadioButton, QtW.QToolButton]


class QBaseButtonWidget(QBaseWidget):
    def __init__(self, mg_widget, qwidg: QButtonWidget):
        super().__init__(mg_widget, qwidg, "isChecked", "setChecked", "toggled")


class CheckBox(QBaseButtonWidget):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QCheckBox)


class PushButton(QBaseButtonWidget):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QPushButton)


class RadioButton(QBaseButtonWidget):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QRadioButton)


class ToolButton(QBaseButtonWidget):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QToolButton)


# NUMBERS

Number = Union[int, float]
QNumberWidget = Union[QtW.QDoubleSpinBox, QtW.QSpinBox, QtW.QSlider]


class QBaseNumberWidget(BaseNumberWidget, QBaseWidget):
    """Provides min/max/step implementations."""

    def __init__(self, mg_widget, qwidg: QNumberWidget):
        super().__init__(mg_widget, qwidg, "value", "setValue", "valueChanged")

    def _mg_get_minimum(self) -> Number:
        """Get the minimum possible value."""
        return self._qwidget.minimum()

    def _mg_set_minimum(self, value: Number):
        """Set the minimum possible value."""
        self._qwidget.setMinimum(value)

    def _mg_get_maximum(self) -> Number:
        """Set the maximum possible value."""
        return self._qwidget.maximum()

    def _mg_set_maximum(self, value: Number):
        """Set the maximum possible value."""
        self._qwidget.setMaximum(value)

    def _mg_get_step(self) -> Number:
        """Get the step size."""
        return self._qwidget.singleStep()

    def _mg_set_step(self, value: Number):
        """Set the step size."""
        self._qwidget.setRange(value)

    def _mg_set_range(self, value: Tuple[Number, Number]):
        """Get the step size."""
        self._qwidget.setRange(value)


class SpinBox(QBaseNumberWidget):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QSpinBox)

    def _mg_set_value(self, value) -> None:
        super()._mg_set_value(int(value))


class FloatSpinBox(QBaseNumberWidget):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QDoubleSpinBox)

    def _mg_set_value(self, value) -> None:
        super()._mg_set_value(float(value))


class Slider(QBaseNumberWidget, QSupportsOrientation):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QSlider)

    def _mg_set_value(self, value) -> None:
        super()._mg_set_value(int(value))


# CATEGORICAL


class Signals(QObject):
    changed = Signal(object)


class ComboBox(QBaseWidget, SupportsChoices):
    def __init__(self, mg_widget):
        super().__init__(mg_widget, QtW.QComboBox, "isChecked", "setCurrentIndex", "")
        self.signals = Signals()
        self._qwidget.currentIndexChanged.connect(self._emit_data)

    def _emit_data(self, index: int):
        data = self._qwidget.itemData(index)
        if data is not None:
            self.signals.changed.emit(data)

    def _mg_bind_change_callback(self, callback):
        self.signals.changed.connect(callback)

    def _mg_get_value(self) -> Any:
        return self._qwidget.itemData(self._qwidget.currentIndex())

    def _mg_set_value(self, value) -> None:
        self._qwidget.setCurrentIndex(self._qwidget.findData(value))

    def _mg_set_choices(self, choices: Iterable[Tuple[str, Any]]) -> None:
        """Set current items in categorical type ``widget`` to ``choices``."""
        # FIXME: still not clearing all old choices correctly.
        names = {x[0] for x in choices}
        for i in range(self._qwidget.count()):
            if self._qwidget.itemText(i) not in names:
                self._qwidget.removeItem(i)
        for name, data in choices:
            if self._qwidget.findText(name) == -1:
                self._qwidget.addItem(name, data)
        current = self._mg_get_value()
        if current not in {x[1] for x in choices}:
            self._qwidget.setCurrentIndex(self._qwidget.findData(choices[0][1]))
            self._qwidget.removeItem(self._qwidget.findData(current))

    def _mg_get_choices(self) -> Tuple[Tuple[str, Any]]:
        """Show the widget."""
        return tuple(
            (self._qwidget.itemText(i), self._qwidget.itemData(i))
            for i in range(self._qwidget.count())
        )


class DateTimeEdit(QBaseWidget):
    def __init__(self, mg_widget):
        super().__init__(
            mg_widget, QtW.QDateTimeEdit, "", "setDateTime", "dateTimeChanged"
        )

    def _mg_get_value(self):
        try:
            return self._qwidget.dateTime().toPython()
        except TypeError:
            return self._qwidget.dateTime().toPyDateTime()


class Layout(BaseLayout, SupportsOrientation):
    def __init__(self, orientation="horizontal"):
        if orientation == "horizontal":
            self._layout: QtW.QLayout = QtW.QHBoxLayout()
        else:
            self._layout = QtW.QFormLayout()

    def _mg_add_widget(self, widget: Widget):
        label = widget.name
        _widget = widget.native
        if isinstance(self._layout, QtW.QFormLayout):
            self._layout.addRow(label, _widget)
        else:
            # if label:
            #     label_widget = QtW.QLabel(label)
            #     label_widget.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
            #     self._layout.addWidget(label_widget)
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
            # if label:
            #     label_widget = QtW.QLabel(label)
            #     label_widget.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
            #     self._layout.insertWidget(position, label_widget)

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
