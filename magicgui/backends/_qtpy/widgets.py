"""Widget implementations (adaptors) for the Qt backend."""
from typing import Any, Iterable, Optional, Tuple, Union

from qtpy import QtWidgets as QtW
from qtpy.QtCore import QObject, Qt, Signal

from magicgui.base import (
    BaseCategoricalWidget,
    BaseContainer,
    BaseRangedWidget,
    BaseValueWidget,
    BaseWidget,
    SupportsOrientation,
)
from magicgui.widget import Widget


class QBaseWidget(BaseWidget):
    """Implements show/hide/native."""

    _qwidget: QtW.QWidget

    def __init__(self, qwidg: QtW.QWidget):
        self._qwidget = qwidg()

    def _mg_show_widget(self):
        self._qwidget.show()

    def _mg_hide_widget(self):
        self._qwidget.hide()

    def _mg_get_native_widget(self):
        return self._qwidget


class QBaseValueWidget(QBaseWidget, BaseValueWidget):
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
        raise NotImplementedError("QLabel has no change signal")

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


class QBaseRangedWidget(QBaseValueWidget, BaseRangedWidget):
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

    def _mg_set_range(self, value: Tuple[float, float]):
        """Get the step size."""
        self._qwidget.setRange(value)


# BUTTONS


class QBaseButtonWidget(QBaseValueWidget):
    _qwidget: Union[QtW.QCheckBox, QtW.QPushButton, QtW.QRadioButton, QtW.QToolButton]

    def __init__(self, qwidg):
        super().__init__(qwidg, "isChecked", "setChecked", "toggled")


class PushButton(QBaseValueWidget):
    def __init__(self):
        super().__init__(QtW.QPushButton, "isChecked", "setChecked", "clicked")


class CheckBox(QBaseButtonWidget):
    def __init__(self):
        super().__init__(QtW.QCheckBox)


class RadioButton(QBaseButtonWidget):
    def __init__(self):
        super().__init__(QtW.QRadioButton)


# class ToolButton(QBaseButtonWidget, BaseToolButton):
#     def __init__(self):
#         super().__init__(QtW.QToolButton)


# CATEGORICAL


class Signals(QObject):
    changed = Signal(object)


class Container(QBaseWidget, BaseContainer, SupportsOrientation):
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


class Slider(QBaseRangedWidget, SupportsOrientation):
    _qwidget: QtW.QSlider

    def __init__(self):
        super().__init__(QtW.QSlider)

    def _mg_set_value(self, value) -> None:
        super()._mg_set_value(int(value))

    def _mg_set_orientation(self, value) -> Any:
        """Get current value of the widget."""
        orientation = Qt.Vertical if value == "vertical" else Qt.Horizontal
        self._qwidget.setOrientation(orientation)

    def _mg_get_orientation(self) -> Any:
        """Get current value of the widget."""
        orientation = self._qwidget.orientation()
        return "vertical" if orientation == Qt.Vertical else "horizontal"


class FloatSlider(Slider):
    """A Slider Widget that can handle float values."""

    PRECISION = 1000

    def _mg_get_value(self) -> float:
        return super()._mg_get_value() / self.PRECISION

    def _mg_set_value(self, value) -> None:
        super()._mg_set_value(int(value * self.PRECISION))

    def _mg_get_minimum(self) -> float:
        """Get the minimum possible value."""
        return super()._mg_get_minimum() / self.PRECISION

    def _mg_set_minimum(self, value: float):
        """Set the minimum possible value."""
        super()._mg_set_minimum(int(value * self.PRECISION))

    def _mg_get_maximum(self) -> float:
        """Set the maximum possible value."""
        return super()._mg_get_maximum() / self.PRECISION

    def _mg_set_maximum(self, value: float):
        """Set the maximum possible value."""
        super()._mg_set_maximum(int(value * self.PRECISION))

    def _mg_get_step(self) -> float:
        """Get the step size."""
        return super()._mg_get_step() / self.PRECISION

    def _mg_set_step(self, value: float):
        """Set the step size."""
        super()._mg_set_step(int(value * self.PRECISION))

    def _mg_set_range(self, value: Tuple[float, float]):
        """Get the step size."""
        _range = (int(value[0] * self.PRECISION), int(value[0] * self.PRECISION))
        super()._mg_set_range(_range)


class ComboBox(QBaseValueWidget, BaseCategoricalWidget):
    _qwidget: QtW.QComboBox

    def __init__(self):
        super().__init__(QtW.QComboBox, "isChecked", "setCurrentIndex", "")
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
