"""Widget implementations (adaptors) for the Qt backend."""
from __future__ import annotations

import math
import re
import warnings
from contextlib import contextmanager
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING, Any, Iterable, Optional, Sequence

import qtpy
import superqt
from qtpy import QtWidgets as QtW
from qtpy.QtCore import QEvent, QObject, Qt, Signal
from qtpy.QtGui import (
    QFont,
    QFontMetrics,
    QImage,
    QKeyEvent,
    QPixmap,
    QResizeEvent,
    QTextDocument,
)

from magicgui.types import FileDialogMode
from magicgui.widgets import _protocols
from magicgui.widgets._bases import Widget


@contextmanager
def _signals_blocked(obj: QtW.QWidget):
    before = obj.blockSignals(True)
    try:
        yield
    finally:
        obj.blockSignals(before)


if TYPE_CHECKING:
    import numpy as np


class EventFilter(QObject):
    parentChanged = Signal()
    valueChanged = Signal(object)

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.ParentChange:
            self.parentChanged.emit()
        return False


class QBaseWidget(_protocols.WidgetProtocol):
    """Implements show/hide/native."""

    _qwidget: QtW.QWidget

    def __init__(
        self, qwidg: type[QtW.QWidget], parent: Optional[QtW.QWidget] = None, **kwargs
    ):
        self._qwidget = qwidg(parent=parent)
        self._qwidget.setObjectName(f"magicgui.{qwidg.__name__}")
        self._event_filter = EventFilter()
        self._qwidget.installEventFilter(self._event_filter)

    def _mgui_close_widget(self):
        self._qwidget.close()

    def _mgui_get_visible(self):
        return self._qwidget.isVisible()

    def _mgui_set_visible(self, value: bool):
        self._qwidget.setVisible(value)

    def _mgui_get_enabled(self) -> bool:
        return self._qwidget.isEnabled()

    def _mgui_set_enabled(self, enabled: bool):
        self._qwidget.setEnabled(enabled)

    # TODO: this used to return _magic_widget ... figure out what we should be returning
    def _mgui_get_parent(self):
        return self._qwidget.parent()

    def _mgui_set_parent(self, widget: Widget):
        self._qwidget.setParent(widget.native if widget else None)

    def _mgui_get_native_widget(self) -> QtW.QWidget:
        return self._qwidget

    def _mgui_get_root_native_widget(self) -> QtW.QWidget:
        return self._qwidget

    def _mgui_get_width(self) -> int:
        """Return the current width of the widget."""
        return self._qwidget.width()

    def _mgui_set_width(self, value: int) -> None:
        """Set the current width of the widget."""
        self._qwidget.resize(int(value), self._qwidget.height())

    def _mgui_get_min_width(self) -> int:
        """Get the minimum allowable width of the widget."""
        return self._qwidget.minimumWidth()

    def _mgui_set_min_width(self, value: int) -> None:
        """Set the minimum allowable width of the widget."""
        self._qwidget.setMinimumWidth(int(value))
        self._qwidget.resize(self._qwidget.sizeHint())

    def _mgui_get_max_width(self) -> int:
        """Get the maximum allowable width of the widget."""
        return self._qwidget.maximumWidth()

    def _mgui_set_max_width(self, value: int) -> None:
        """Set the maximum allowable width of the widget."""
        self._qwidget.setMaximumWidth(int(value))
        self._qwidget.resize(self._qwidget.sizeHint())

    def _mgui_get_height(self) -> int:
        """Return the current height of the widget."""
        return self._qwidget.height()

    def _mgui_set_height(self, value: int) -> None:
        """Set the current height of the widget."""
        self._qwidget.resize(self._qwidget.width(), int(value))

    def _mgui_get_min_height(self) -> int:
        """Get the minimum allowable height of the widget."""
        return self._qwidget.minimumHeight()

    def _mgui_set_min_height(self, value: int) -> None:
        """Set the minimum allowable height of the widget."""
        self._qwidget.setMinimumHeight(int(value))
        self._qwidget.resize(self._qwidget.sizeHint())

    def _mgui_get_max_height(self) -> int:
        """Get the maximum allowable height of the widget."""
        return self._qwidget.maximumHeight()

    def _mgui_set_max_height(self, value: int) -> None:
        """Set the maximum allowable height of the widget."""
        self._qwidget.setMaximumHeight(int(value))
        self._qwidget.resize(self._qwidget.sizeHint())

    def _mgui_get_tooltip(self) -> str:
        return self._qwidget.toolTip()

    def _mgui_set_tooltip(self, value: Optional[str]) -> None:
        self._qwidget.setToolTip(str(value) if value else None)

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
        if qtpy.API_NAME.startswith("PySide"):
            arr = np.array(bits).reshape(h, w, c)
        else:
            bits.setsize(h * w * c)
            arr = np.frombuffer(bits, np.uint8).reshape(h, w, c)

        return arr[:, :, [2, 1, 0, 3]]


class QBaseValueWidget(QBaseWidget, _protocols.ValueWidgetProtocol):
    """Implements get/set/bind_change."""

    def __init__(
        self, qwidg: QtW.QWidget, getter: str, setter: str, onchange: str, **kwargs
    ):
        super().__init__(qwidg, **kwargs)
        self._getter_name = getter
        self._setter_name = setter
        self._onchange_name = onchange

    def _mgui_get_value(self) -> Any:
        val = getattr(self._qwidget, self._getter_name)()
        return self._post_get_hook(val)

    def _mgui_set_value(self, value) -> None:
        val = self._pre_set_hook(value)
        getattr(self._qwidget, self._setter_name)(val)

    def _mgui_bind_change_callback(self, callback):
        signal_instance = getattr(self._qwidget, self._onchange_name, None)
        if signal_instance:
            signal_instance.connect(callback)

    def _post_get_hook(self, value):
        return value

    def _pre_set_hook(self, value):
        return value


# BASE WIDGET


class EmptyWidget(QBaseWidget):
    def __init__(self, **kwargs):
        super().__init__(QtW.QWidget, **kwargs)

    def _mgui_get_value(self) -> Any:
        raise NotImplementedError()

    def _mgui_set_value(self, value) -> None:
        raise NotImplementedError()

    def _mgui_bind_change_callback(self, callback):
        pass


# STRING WIDGETS


class QBaseStringWidget(QBaseValueWidget):
    _qwidget: QtW.QLineEdit | QtW.QTextEdit | QtW.QLabel

    def _mgui_set_value(self, value) -> None:
        super()._mgui_set_value(str(value))


class Label(QBaseStringWidget):
    _qwidget: QtW.QLabel

    def __init__(self, **kwargs):
        super().__init__(QtW.QLabel, "text", "setText", "", **kwargs)
        self._qwidget.setSizePolicy(QtW.QSizePolicy.Fixed, QtW.QSizePolicy.Fixed)

    def _mgui_bind_change_callback(self, callback):
        # raise NotImplementedError("QLabel has no change signal")
        pass

    def _mgui_set_value(self, value) -> None:
        super()._mgui_set_value(str(value))


class _ResizeableLabel(QtW.QLabel):
    resized = Signal()

    def resizeEvent(self, a0: QResizeEvent) -> None:
        self.resized.emit()
        return super().resizeEvent(a0)


class Image(QBaseValueWidget):
    _qwidget: _ResizeableLabel

    def __init__(self, **kwargs):
        super().__init__(_ResizeableLabel, "text", "setText", "", **kwargs)
        self._qwidget.setSizePolicy(QtW.QSizePolicy.Ignored, QtW.QSizePolicy.Ignored)
        self._qwidget.resized.connect(self._rescale)
        self._pixmap: QPixmap = None

    def _rescale(self):
        if self._pixmap:
            sz = self._qwidget.size()
            self._qwidget.setPixmap(
                self._pixmap.scaled(sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

    def _mgui_set_value(self, val: np.ndarray) -> None:
        image = QImage(val, val.shape[1], val.shape[0], QImage.Format_RGBA8888)
        self._pixmap = QPixmap.fromImage(image)
        self._rescale()


class LineEdit(QBaseStringWidget):
    _qwidget: QtW.QLineEdit

    def __init__(self, **kwargs):
        super().__init__(QtW.QLineEdit, "text", "setText", "textChanged", **kwargs)


class LiteralEvalLineEdit(QBaseStringWidget):
    _qwidget: QtW.QLineEdit

    def __init__(self, **kwargs):
        super().__init__(QtW.QLineEdit, "text", "setText", "textChanged", **kwargs)

    def _post_get_hook(self, value):
        from ast import literal_eval

        return literal_eval(value)


class TextEdit(QBaseStringWidget, _protocols.SupportsReadOnly):
    def __init__(self, **kwargs):
        super().__init__(
            QtW.QTextEdit, "toPlainText", "setText", "textChanged", **kwargs
        )

    def _mgui_set_read_only(self, value: bool) -> None:
        self._qwidget.setReadOnly(value)

    def _mgui_get_read_only(self) -> bool:
        return self._qwidget.isReadOnly()


# NUMBERS


class QBaseRangedWidget(QBaseValueWidget, _protocols.RangedWidgetProtocol):
    """Provides min/max/step implementations."""

    _qwidget: QtW.QDoubleSpinBox | QtW.QSpinBox | QtW.QAbstractSlider
    _precision: float = 1

    def __init__(self, qwidg, **kwargs):
        super().__init__(qwidg, "value", "setValue", "valueChanged", **kwargs)

    def _mgui_get_min(self) -> float:
        """Get the minimum possible value."""
        val = self._qwidget.minimum()
        return self._post_get_hook(val)

    def _mgui_set_min(self, value: float):
        """Set the minimum possible value."""
        self._update_precision(minimum=value)
        val = self._pre_set_hook(value)
        self._qwidget.setMinimum(val)

    def _mgui_get_max(self) -> float:
        """Set the maximum possible value."""
        val = self._qwidget.maximum()
        return self._post_get_hook(val)

    def _mgui_set_max(self, value: float):
        """Set the maximum possible value."""
        self._update_precision(maximum=value)
        val = self._pre_set_hook(value)
        self._qwidget.setMaximum(val)

    def _mgui_get_step(self) -> float:
        """Get the step size."""
        val = self._qwidget.singleStep()
        return self._post_get_hook(val)

    def _mgui_set_adaptive_step(self, value: bool):
        """Seti is widget single steep should be adaptive."""
        self._qwidget.setStepType(
            QtW.QAbstractSpinBox.AdaptiveDecimalStepType
            if value
            else QtW.QAbstractSpinBox.DefaultStepType
        )

    def _mgui_get_adaptive_step(self) -> bool:
        """Get is widget single steep should be adaptive."""
        return self._qwidget.stepType() == QtW.QAbstractSpinBox.AdaptiveDecimalStepType

    def _mgui_set_step(self, value: float):
        """Set the step size."""
        self._update_precision(step=value)
        val = self._pre_set_hook(value)
        self._qwidget.setSingleStep(val)

    def _update_precision(self, **kwargs):
        pass


# BUTTONS


class QBaseButtonWidget(QBaseValueWidget, _protocols.SupportsText):
    _qwidget: QtW.QCheckBox | QtW.QPushButton | QtW.QRadioButton | QtW.QToolButton

    def __init__(self, qwidg, **kwargs):
        super().__init__(qwidg, "isChecked", "setChecked", "toggled", **kwargs)

    def _mgui_set_text(self, value: str) -> None:
        """Set text."""
        self._qwidget.setText(str(value))

    def _mgui_get_text(self) -> str:
        """Get text."""
        return self._qwidget.text()


class PushButton(QBaseButtonWidget):
    def __init__(self, **kwargs):
        QBaseValueWidget.__init__(
            self, QtW.QPushButton, "isChecked", "setChecked", "clicked", **kwargs
        )
        # make enter/return "click" the button when focused.
        self._qwidget.setAutoDefault(True)


class CheckBox(QBaseButtonWidget):
    def __init__(self, **kwargs):
        super().__init__(QtW.QCheckBox, **kwargs)


class RadioButton(QBaseButtonWidget):
    def __init__(self, **kwargs):
        super().__init__(QtW.QRadioButton, **kwargs)


# class ToolButton(QBaseButtonWidget):
#     def __init__(self,**kwargs):
#         super().__init__(QtW.QToolButton, **kwargs)


class Container(
    QBaseWidget, _protocols.ContainerProtocol, _protocols.SupportsOrientation
):
    def __init__(self, layout="vertical", scrollable: bool = False, **kwargs):
        QBaseWidget.__init__(self, QtW.QWidget, **kwargs)
        if layout == "horizontal":
            self._layout: QtW.QBoxLayout = QtW.QHBoxLayout()
        else:
            self._layout = QtW.QVBoxLayout()
        self._qwidget.setLayout(self._layout)

        if scrollable:
            self._scroll = QtW.QScrollArea()
            # Allow widget to resize when window is larger than min widget size
            self._scroll.setWidgetResizable(True)
            if layout == "horizontal":
                horiz_policy = Qt.ScrollBarAsNeeded
                vert_policy = Qt.ScrollBarAlwaysOff
            else:
                horiz_policy = Qt.ScrollBarAlwaysOff
                vert_policy = Qt.ScrollBarAsNeeded
            self._scroll.setHorizontalScrollBarPolicy(horiz_policy)
            self._scroll.setVerticalScrollBarPolicy(vert_policy)
            self._scroll.setWidget(self._qwidget)
            self._qwidget = self._scroll

    @property
    def _is_scrollable(self) -> bool:
        return isinstance(self._qwidget, QtW.QScrollArea)

    def _mgui_get_root_native_widget(self):
        return self._qwidget

    def _mgui_get_native_widget(self):
        # Return widget with the layout set
        return self._qwidget.widget() if self._is_scrollable else self._qwidget

    def _mgui_get_visible(self):
        return self._mgui_get_native_widget().isVisible()

    def _mgui_insert_widget(self, position: int, widget: Widget):
        self._layout.insertWidget(position, widget.native)
        if self._is_scrollable:
            min_size = self._layout.totalMinimumSize()
            if isinstance(self._layout, QtW.QHBoxLayout):
                self._scroll.setMinimumHeight(min_size.height())
            else:
                self._scroll.setMinimumWidth(min_size.width() + 20)

    def _mgui_remove_widget(self, widget: Widget):
        self._layout.removeWidget(widget.native)
        widget.native.setParent(None)

    def _mgui_get_margins(self) -> tuple[int, int, int, int]:
        m = self._layout.contentsMargins()
        return m.left(), m.top(), m.right(), m.bottom()

    def _mgui_set_margins(self, margins: tuple[int, int, int, int]) -> None:
        self._layout.setContentsMargins(*margins)

    def _mgui_set_orientation(self, value) -> None:
        """Set orientation, value will be 'horizontal' or 'vertical'."""
        raise NotImplementedError(
            "Sorry, changing orientation after instantiation "
            "is not yet implemented for Qt."
        )

    def _mgui_get_orientation(self) -> str:
        """Set orientation, return either 'horizontal' or 'vertical'."""
        if isinstance(self, QtW.QHBoxLayout):
            return "horizontal"
        else:
            return "vertical"


class MainWindow(Container):
    def __init__(self, layout="vertical", scrollable: bool = False, **kwargs):
        super().__init__(layout=layout, scrollable=scrollable, **kwargs)
        self._main_window = QtW.QMainWindow()
        self._menus: dict[str, QtW.QMenu] = {}
        if scrollable:
            self._main_window.setCentralWidget(self._scroll)
        else:
            self._main_window.setCentralWidget(self._qwidget)

    def _mgui_get_visible(self):
        return self._main_window.isVisible()

    def _mgui_set_visible(self, value: bool):
        self._main_window.setVisible(value)

    def _mgui_get_native_widget(self) -> QtW.QMainWindow:
        return self._main_window

    def _mgui_create_menu_item(
        self, menu_name: str, action_name: str, callback=None, shortcut=None
    ):
        menu = self._menus.setdefault(
            menu_name, self._main_window.menuBar().addMenu(f"&{menu_name}")
        )
        action = QtW.QAction(action_name, self._main_window)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if callback is not None:
            action.triggered.connect(callback)
        menu.addAction(action)


class SpinBox(QBaseRangedWidget):
    def __init__(self, **kwargs):
        super().__init__(QtW.QSpinBox, **kwargs)

    def _mgui_set_value(self, value) -> None:
        super()._mgui_set_value(int(value))

    def _pre_set_hook(self, value):
        return int(value)


class FloatSpinBox(QBaseRangedWidget):
    def __init__(self, **kwargs):
        super().__init__(QtW.QDoubleSpinBox, **kwargs)

    def _mgui_set_value(self, value) -> None:
        super()._mgui_set_value(float(value))

    def _mgui_set_step(self, value: float):
        """Set the step size."""
        if value and value < 1 * 10 ** -self._qwidget.decimals():
            self._qwidget.setDecimals(math.ceil(abs(math.log10(value))))
        self._qwidget.setSingleStep(value)


class _Slider(QBaseRangedWidget, _protocols.SupportsOrientation):
    _qwidget: QtW.QSlider

    def __init__(
        self,
        qwidg=QtW.QSlider,
        readout: bool = True,
        orientation: str = "horizontal",
        **kwargs,
    ):
        super().__init__(qwidg, **kwargs)
        self._mgui_set_orientation("horizontal")
        self._mgui_set_readout_visibility(readout)
        self._mgui_set_orientation(orientation)

    def _mgui_set_orientation(self, value) -> Any:
        """Get current value of the widget."""
        orientation = Qt.Vertical if value == "vertical" else Qt.Horizontal
        self._qwidget.setOrientation(orientation)

    def _mgui_get_orientation(self) -> Any:
        """Get current value of the widget."""
        orientation = self._qwidget.orientation()
        return "vertical" if orientation == Qt.Vertical else "horizontal"

    def _mgui_set_readout_visibility(self, value: bool):
        raise NotImplementedError()

    def _mgui_get_tracking(self) -> bool:
        # Progressbar also uses this base, but doesn't have tracking
        if hasattr(self._qwidget, "hasTracking"):
            return self._qwidget.hasTracking()
        return False

    def _mgui_set_tracking(self, value: bool) -> None:
        # Progressbar also uses this base, but doesn't have tracking
        if hasattr(self._qwidget, "setTracking"):
            self._qwidget.setTracking(value)

    def _pre_set_hook(self, value):
        return self._cast(value)

    def _cast(self, value: Any) -> Any:
        return int(value)


class Slider(_Slider):
    _qwidget: QtW.QSlider
    _readout = QtW.QSpinBox

    def __init__(self, qwidg=QtW.QSlider, **kwargs):
        self._container = QtW.QWidget()
        self._readout_widget = self._readout()
        super().__init__(qwidg, **kwargs)

        self._readout_widget.setButtonSymbols(self._readout_widget.NoButtons)
        self._readout_widget.setStyleSheet("background:transparent; border: 0;")

        self._qwidget.valueChanged.connect(self._on_slider_change)
        self._readout_widget.editingFinished.connect(self._on_readout_change)

    def _mgui_get_visible(self):
        return self._container.isVisible()

    def _mgui_set_visible(self, value: bool):
        self._container.setVisible(value)

    def _mgui_set_orientation(self, value: str) -> None:
        """Set orientation, value will be 'horizontal' or 'vertical'."""
        if value == "vertical":
            layout = QtW.QVBoxLayout()
            self._qwidget.setOrientation(Qt.Vertical)
            layout.addWidget(self._qwidget, alignment=Qt.AlignHCenter)
            layout.addWidget(self._readout_widget, alignment=Qt.AlignHCenter)
            self._readout_widget.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(1)
        else:
            layout = QtW.QHBoxLayout()
            self._qwidget.setOrientation(Qt.Horizontal)
            layout.addWidget(self._qwidget)
            layout.addWidget(self._readout_widget)
            self._readout_widget.setAlignment(Qt.AlignRight)
            right_margin = 0 if self._readout_widget.isVisible() else 4
            layout.setContentsMargins(0, 0, right_margin, 0)
            layout.setSpacing(4)
        old_layout = self._container.layout()
        if old_layout is not None:
            QtW.QWidget().setLayout(old_layout)
        self._container.setLayout(layout)

    def _on_slider_change(self, value):
        self._readout_widget.setValue(self._post_get_hook(value))

    def _on_readout_change(self):
        self._qwidget.setValue(self._pre_set_hook(self._readout_widget.value()))

    def _mgui_get_native_widget(self) -> QtW.QWidget:
        return self._container

    def _mgui_set_min(self, value: float):
        """Set the minimum possible value."""
        super()._mgui_set_min(value)
        self._readout_widget.setMinimum(self._cast(value))

    def _mgui_set_max(self, value: float):
        """Set the maximum possible value."""
        super()._mgui_set_max(value)
        self._readout_widget.setMaximum(self._cast(value))

    def _mgui_set_step(self, value: float):
        """Set the step size."""
        super()._mgui_set_step(value)
        self._readout_widget.setSingleStep(self._cast(value))

    def _mgui_get_adaptive_step(self) -> bool:
        return (
            self._readout_widget.stepType()
            == QtW.QAbstractSpinBox.AdaptiveDecimalStepType
        )

    def _mgui_set_adaptive_step(self, value: bool):
        self._readout_widget.setStepType(
            QtW.QAbstractSpinBox.AdaptiveDecimalStepType
            if value
            else QtW.QAbstractSpinBox.DefaultStepType
        )

    def _mgui_set_readout_visibility(self, value: bool):
        self._readout_widget.show() if value else self._readout_widget.hide()


class FloatSlider(Slider):
    _readout = QtW.QDoubleSpinBox
    _precision = 1e6

    def _update_precision(self, minimum=None, maximum=None, step=None):
        """Called when min/max/step is changed.

        _precision is the factor that converts from integer representation in the slider
        widget, to the actual float representation needed.
        """
        orig = self._precision

        if minimum is not None or maximum is not None:
            _min = minimum or self._mgui_get_min()
            _max = maximum or self._mgui_get_max()

            # make sure val * precision is within int32 overflow limit for Qt
            val = max([abs(_min), abs(_max)])
            while abs(self._precision * val) >= 2**32 // 2:
                self._precision *= 0.1
        elif step:
            while step < (1 / self._precision):
                self._precision *= 10

        ratio = self._precision / orig
        if ratio != 1:
            self._mgui_set_value(self._mgui_get_value() * ratio)
            if not step:
                self._mgui_set_max(self._mgui_get_max() * ratio)
                self._mgui_set_min(self._mgui_get_min() * ratio)
            # self._mgui_set_step(self._mgui_get_step() * ratio)

    def _cast(self, value: Any) -> Any:
        return float(value)

    def _post_get_hook(self, value):
        return value / self._precision

    def _pre_set_hook(self, value):
        return int(value * self._precision)

    def _mgui_bind_change_callback(self, callback):
        def _converted_value(value):
            callback(self._post_get_hook(value))

        self._qwidget.valueChanged.connect(_converted_value)


class RangeSlider(_Slider):
    _qwidget: superqt.QLabeledRangeSlider

    def __init__(self, **kwargs):
        super().__init__(superqt.QLabeledRangeSlider, **kwargs)
        if hasattr(self._qwidget, "applyMacStylePatch"):
            # >= magicgui v0.5.2
            self._qwidget.applyMacStylePatch()

    def _mgui_set_readout_visibility(self, value: bool):
        method = "show" if value else "hide"
        try:
            for label in chain(
                self._qwidget._handle_labels,
                [self._qwidget._min_label, self._qwidget._max_label],
            ):
                getattr(label, method)()
        except AttributeError as e:
            warnings.warn(str(e))

    def _mgui_set_adaptive_step(self, value: bool):
        pass

    def _mgui_get_adaptive_step(self) -> bool:
        return False

    def _pre_set_hook(self, value):
        return value


class FloatRangeSlider(RangeSlider):
    _qwidget: superqt.QLabeledDoubleRangeSlider

    def __init__(self, **kwargs):
        _Slider.__init__(self, superqt.QLabeledDoubleRangeSlider, **kwargs)
        if hasattr(self._qwidget, "applyMacStylePatch"):
            # >= magicgui v0.5.2
            self._qwidget.applyMacStylePatch()


class ProgressBar(_Slider):
    _qwidget: QtW.QProgressBar

    def __init__(self, **kwargs):
        super().__init__(QtW.QProgressBar, **kwargs)

    def _mgui_get_step(self) -> float:
        """Get the step size."""
        return 1

    def _mgui_set_step(self, value: float):
        """Set the step size."""

    def _mgui_set_adaptive_step(self, value: bool):
        """Set is step is adaptive"""

    def _mgui_get_adaptive_step(self) -> bool:
        return False

    def _mgui_set_readout_visibility(self, value: bool):
        self._qwidget.setTextVisible(value)


class ComboBox(QBaseValueWidget, _protocols.CategoricalWidgetProtocol):
    _qwidget: QtW.QComboBox

    def __init__(self, **kwargs):
        super().__init__(QtW.QComboBox, "isChecked", "setCurrentIndex", "", **kwargs)
        self._qwidget.currentIndexChanged.connect(self._emit_data)

    def _emit_data(self, index: int):
        self._event_filter.valueChanged.emit(self._qwidget.itemData(index))

    def _mgui_bind_change_callback(self, callback):
        self._event_filter.valueChanged.connect(callback)

    def _mgui_get_count(self) -> int:
        """Return the number of items in the dropdown."""
        return self._qwidget.count()

    def _mgui_get_choice(self, choice_name: str) -> Any:
        item_index = self._qwidget.findText(choice_name)
        return None if item_index == -1 else self._qwidget.itemData(item_index)

    def _mgui_get_current_choice(self) -> str:
        return self._qwidget.itemText(self._qwidget.currentIndex())

    def _mgui_get_value(self) -> Any:
        return self._qwidget.itemData(self._qwidget.currentIndex())

    def _mgui_set_value(self, value) -> None:
        # Note: there's a bug in PyQt6, where CombBox.findData(value) will not
        # find the data if value is an Enum. So we do it manually
        wdg = self._qwidget
        idx = next((i for i in range(wdg.count()) if wdg.itemData(i) == value), -1)
        self._qwidget.setCurrentIndex(idx)

    def _mgui_set_choice(self, choice_name: str, data: Any) -> None:
        """Set data for ``choice_name``."""
        item_index = self._qwidget.findText(choice_name)
        # if it's not in the list, add a new item
        if item_index == -1:
            self._qwidget.addItem(choice_name, data)
        # otherwise update its data
        else:
            self._qwidget.setItemData(item_index, data)

    def _mgui_set_choices(self, choices: Iterable[tuple[str, Any]]) -> None:
        """Set current items in categorical type ``widget`` to ``choices``."""
        choices_ = list(choices)
        if not choices_:
            self._qwidget.clear()
            return

        with _signals_blocked(self._qwidget):
            choice_names = [x[0] for x in choices_]
            # remove choices that no longer exist
            current = self._qwidget.itemText(self._qwidget.currentIndex())
            for i in reversed(range(self._qwidget.count())):
                if self._qwidget.itemText(i) not in choice_names:
                    self._qwidget.removeItem(i)
            # update choices
            for name, data in choices_:
                self._mgui_set_choice(name, data)

            # if the currently selected item is not in the new set,
            # remove it and select the first item in the list
            current2 = self._qwidget.itemText(self._qwidget.currentIndex())
            if current not in choice_names:
                # previous value was not in the new choices so set first element
                first = choice_names[0]
                self._qwidget.setCurrentIndex(self._qwidget.findText(first))
            elif current2 != current:
                # element is present but order is different
                self._qwidget.setCurrentIndex(self._qwidget.findText(current))
        if current not in choice_names:
            self._emit_data(self._qwidget.currentIndex())

    def _mgui_del_choice(self, choice_name: str) -> None:
        """Delete choice_name."""
        item_index = self._qwidget.findText(choice_name)
        if item_index >= 0:
            self._qwidget.removeItem(item_index)

    def _mgui_get_choices(self) -> tuple[tuple[str, Any], ...]:
        """Get available choices."""
        return tuple(
            (self._qwidget.itemText(i), self._qwidget.itemData(i))
            for i in range(self._qwidget.count())
        )


class Select(QBaseValueWidget, _protocols.CategoricalWidgetProtocol):
    _qwidget: QtW.QListWidget

    def __init__(self, **kwargs):
        super().__init__(QtW.QListWidget, "isChecked", "setCurrentIndex", "", **kwargs)
        self._qwidget.itemSelectionChanged.connect(self._emit_data)
        self._qwidget.setSelectionMode(QtW.QAbstractItemView.ExtendedSelection)

    def _emit_data(self):
        data = self._qwidget.selectedItems()
        self._event_filter.valueChanged.emit(
            [d.data(Qt.ItemDataRole.UserRole) for d in data]
        )

    def _mgui_bind_change_callback(self, callback):
        self._event_filter.valueChanged.connect(callback)

    def _mgui_get_count(self) -> int:
        """Return the number of items in the dropdown."""
        return self._qwidget.count()

    def _mgui_get_choice(self, choice_name: str) -> list[Any]:
        items = self._qwidget.findItems(choice_name, Qt.MatchExactly)
        return [i.data(Qt.ItemDataRole.UserRole) for i in items]

    def _mgui_get_current_choice(self) -> list[str]:  # type: ignore[override]
        return [i.text() for i in self._qwidget.selectedItems()]

    def _mgui_get_value(self) -> Any:
        return [i.data(Qt.ItemDataRole.UserRole) for i in self._qwidget.selectedItems()]

    def _mgui_set_value(self, value) -> None:
        if not isinstance(value, (list, tuple)):
            value = [value]
        selected_prev = self._qwidget.selectedItems()
        with _signals_blocked(self._qwidget):
            for i in range(self._qwidget.count()):
                item = self._qwidget.item(i)
                item.setSelected(item.data(Qt.ItemDataRole.UserRole) in value)
        selected_post = self._qwidget.selectedItems()
        if selected_prev != selected_post:
            self._emit_data()

    def _mgui_set_choice(self, choice_name: str, data: Any) -> None:
        """Set data for ``choice_name``."""
        items = self._qwidget.findItems(choice_name, Qt.MatchExactly)
        # if it's not in the list, add a new item
        if not items:
            item = QtW.QListWidgetItem(choice_name)
            item.setData(Qt.ItemDataRole.UserRole, data)
            self._qwidget.addItem(item)
        # otherwise update its data
        else:
            for item in items:
                item.setData(Qt.ItemDataRole.UserRole, data)

    def _mgui_set_choices(self, choices: Iterable[tuple[str, Any]]) -> None:
        """Set current items in categorical type ``widget`` to ``choices``."""
        choices_ = list(choices)
        if not choices_:
            self._qwidget.clear()
            return

        with _signals_blocked(self._qwidget):
            choice_names = [x[0] for x in choices_]
            selected_prev = self._qwidget.selectedItems()
            # remove choices that no longer exist
            for i in reversed(range(self._qwidget.count())):
                if self._qwidget.item(i).text() not in choice_names:
                    self._qwidget.takeItem(i)
            # update choices
            for name, data in choices_:
                self._mgui_set_choice(name, data)
            selected_post = self._qwidget.selectedItems()
        if selected_prev != selected_post:
            self._emit_data()

    def _mgui_del_choice(self, choice_name: str) -> None:
        """Delete choice_name."""
        for i in reversed(range(self._qwidget.count())):
            if self._qwidget.item(i).text() == choice_name:
                self._qwidget.takeItem(i)

    def _mgui_get_choices(self) -> tuple[tuple[str, Any], ...]:
        """Get available choices."""
        return tuple(
            (
                self._qwidget.item(i).text(),
                self._qwidget.item(i).data(Qt.ItemDataRole.UserRole),
            )
            for i in range(self._qwidget.count())
        )


class RadioButtons(
    QBaseValueWidget,
    _protocols.CategoricalWidgetProtocol,
    _protocols.SupportsOrientation,
):
    _qwidget: QtW.QGroupBox

    def __init__(self, **kwargs):
        super().__init__(QtW.QGroupBox, "", "", "", **kwargs)
        self._btn_group = QtW.QButtonGroup(self._qwidget)
        self._mgui_set_orientation("vertical")
        self._btn_group.buttonToggled.connect(self._emit_data)

    def _emit_data(self, btn, checked):
        if checked:
            self._event_filter.valueChanged.emit(self._mgui_get_value())

    def _mgui_bind_change_callback(self, callback):
        self._event_filter.valueChanged.connect(callback)

    def _mgui_set_orientation(self, value: str) -> None:
        """Set orientation, value will be 'horizontal' or 'vertical'."""
        new_layout = QtW.QHBoxLayout() if value == "horizontal" else QtW.QVBoxLayout()
        for btn in self._btn_group.buttons():
            new_layout.addWidget(btn)
        old_layout = self._qwidget.layout()
        if old_layout is not None:
            QtW.QWidget().setLayout(old_layout)
        self._qwidget.setLayout(new_layout)
        self._qwidget.layout().setContentsMargins(4, 4, 4, 4)

    def _mgui_get_orientation(self) -> str:
        """Get orientation, return either 'horizontal' or 'vertical'."""
        if isinstance(self._qwidget.layout(), QtW.QVBoxLayout):
            return "vertical"
        else:
            return "horizontal"

    def _mgui_get_current_choice(self) -> str:
        btn = self._btn_group.checkedButton()
        return btn.text() if btn else None

    def _mgui_get_value(self) -> Any:
        btn = self._btn_group.checkedButton()
        return btn._data if btn else None

    def _mgui_set_value(self, value) -> None:
        for btn in self._btn_group.buttons():
            if btn._data == value:
                btn.setChecked(True)
                break  # exclusive

    def _mgui_get_count(self) -> int:
        """Return the number of items in the dropdown."""
        return len(self._btn_group.buttons())

    def _mgui_get_choice(self, choice_name: str) -> Any:
        for btn in self._btn_group.buttons():
            if btn.text() == choice_name:
                return btn._data
        return None

    def _add_button(self, label: str, data: Any = None):
        btn = QtW.QRadioButton(label, self._qwidget)
        btn._data = data
        self._btn_group.addButton(btn)
        self._qwidget.layout().addWidget(btn)

    def _remove_button(self, btn):
        self._btn_group.removeButton(btn)
        btn.setParent(None)
        btn.deleteLater()

    def _mgui_set_choice(self, choice_name: str, data: Any) -> None:
        """Set data for ``choice_name``."""
        for btn in self._btn_group.buttons():
            if btn.text() == choice_name:
                # otherwise update its data
                btn._data = data
        else:
            # if it's not in the list, add a new item
            self._add_button(choice_name, data)

    def _mgui_del_choice(self, choice_name: str) -> None:
        """Delete choice_name."""
        for btn in self._btn_group.buttons():
            if btn.text() == choice_name:
                self._remove_button(btn)
                break

    def _mgui_get_choices(self) -> tuple[tuple[str, Any], ...]:
        """Get available choices."""
        return tuple((str(btn.text()), btn._data) for btn in self._btn_group.buttons())

    def _mgui_set_choices(self, choices: Iterable[tuple[str, Any]]) -> None:
        """Set current items in categorical type ``widget`` to ``choices``."""
        current = self._mgui_get_value()
        for btn in self._btn_group.buttons():
            self._remove_button(btn)

        for c in choices:
            self._add_button(*c)
        self._mgui_set_value(current)


class DateTimeEdit(QBaseValueWidget):
    def __init__(self, **kwargs):
        super().__init__(
            QtW.QDateTimeEdit, "", "setDateTime", "dateTimeChanged", **kwargs
        )

    def _mgui_get_value(self):
        try:
            return self._qwidget.dateTime().toPython()
        except (TypeError, AttributeError):
            return self._qwidget.dateTime().toPyDateTime()


class DateEdit(QBaseValueWidget):
    def __init__(self, **kwargs):
        super().__init__(QtW.QDateEdit, "", "setDate", "dateChanged", **kwargs)

    def _mgui_get_value(self):
        try:
            return self._qwidget.date().toPython()
        except (TypeError, AttributeError):
            return self._qwidget.date().toPyDate()


class TimeEdit(QBaseValueWidget):
    def __init__(self, **kwargs):
        super().__init__(QtW.QTimeEdit, "", "setTime", "timeChanged", **kwargs)

    def _mgui_get_value(self):
        try:
            return self._qwidget.time().toPython()
        except (TypeError, AttributeError):
            return self._qwidget.time().toPyTime()


class Dialog(QBaseWidget, _protocols.ContainerProtocol):
    def __init__(self, layout="vertical", scrollable: bool = False, **kwargs):
        QBaseWidget.__init__(self, QtW.QDialog, **kwargs)
        if layout == "horizontal":
            self._layout: QtW.QBoxLayout = QtW.QHBoxLayout()
        else:
            self._layout = QtW.QVBoxLayout()
        self._qwidget.setLayout(self._layout)
        self._layout.setSizeConstraint(QtW.QLayout.SizeConstraint.SetMinAndMaxSize)

        button_box = QtW.QDialogButtonBox(
            QtW.QDialogButtonBox.StandardButton.Ok
            | QtW.QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self._qwidget,
        )
        button_box.accepted.connect(self._qwidget.accept)
        button_box.rejected.connect(self._qwidget.reject)
        self._layout.addWidget(button_box)

    def _mgui_insert_widget(self, position: int, widget: Widget):
        self._layout.insertWidget(position, widget.native)

    def _mgui_remove_widget(self, widget: Widget):
        self._layout.removeWidget(widget.native)
        widget.native.setParent(None)

    def _mgui_get_margins(self) -> tuple[int, int, int, int]:
        m = self._layout.contentsMargins()
        return m.left(), m.top(), m.right(), m.bottom()

    def _mgui_set_margins(self, margins: tuple[int, int, int, int]) -> None:
        self._layout.setContentsMargins(*margins)

    def _mgui_set_orientation(self, value) -> None:
        """Set orientation, value will be 'horizontal' or 'vertical'."""
        raise NotImplementedError("Setting orientation not supported for dialogs.")

    def _mgui_get_orientation(self) -> str:
        """Set orientation, return either 'horizontal' or 'vertical'."""
        return "horizontal" if isinstance(self, QtW.QHBoxLayout) else "vertical"

    def _mgui_exec(self) -> Any:
        return self._qwidget.exec_()


QFILE_DIALOG_MODES = {
    FileDialogMode.EXISTING_FILE: QtW.QFileDialog.getOpenFileName,
    FileDialogMode.EXISTING_FILES: QtW.QFileDialog.getOpenFileNames,
    FileDialogMode.OPTIONAL_FILE: QtW.QFileDialog.getSaveFileName,
    FileDialogMode.EXISTING_DIRECTORY: QtW.QFileDialog.getExistingDirectory,
}


def show_file_dialog(
    mode: str | FileDialogMode = FileDialogMode.EXISTING_FILE,
    caption: str = None,
    start_path: str = None,
    filter: str = None,
    parent=None,
) -> str | None:
    show_dialog = QFILE_DIALOG_MODES[FileDialogMode(mode)]
    if mode is FileDialogMode.EXISTING_DIRECTORY:
        result = show_dialog(parent, caption, start_path)
    else:
        result, _ = show_dialog(parent, caption, start_path, filter)
    return result or None


def _might_be_rich_text(text):
    return bool(re.search("<[^\n]+>", text))


def get_text_width(text: str) -> int:
    """Return the width required to render ``text`` (including rich text elements)."""
    if _might_be_rich_text(text):
        doc = QTextDocument()
        doc.setHtml(text)
        return math.ceil(doc.size().width())
    else:
        fm = QFontMetrics(QFont("", 0))
        return fm.boundingRect(text).width() + 5


def _maybefloat(item):
    if not item:
        return None
    num = item.text() if hasattr(item, "text") else item
    try:
        return int(num) if num.isdigit() else float(num)
    except ValueError:
        return num


class _QTableExtended(QtW.QTableWidget):
    _read_only: bool = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setItemDelegate(_ItemDelegate(parent=self))

    def _copy_to_clipboard(self):
        selranges = self.selectedRanges()
        if not selranges:
            return
        if len(selranges) > 1:
            import warnings

            warnings.warn(
                "Multiple table selections detected: "
                "only the first (upper left) selection will be copied"
            )

        # copy first selection range
        sel = selranges[0]
        lines = []
        for r in range(sel.topRow(), sel.bottomRow() + 1):
            cells = []
            for c in range(sel.leftColumn(), sel.rightColumn() + 1):
                item = self.item(r, c)
                cells.append(item.text()) if hasattr(item, "text") else ""
            lines.append("\t".join(cells))

        if lines:
            QtW.QApplication.clipboard().setText("\n".join(lines))

    def _paste_from_clipboard(self):
        if self._read_only:
            return

        sel_idx = self.selectedIndexes()
        if not sel_idx:
            return
        text = QtW.QApplication.clipboard().text()
        if not text:
            return

        # paste in the text
        row0, col0 = sel_idx[0].row(), sel_idx[0].column()
        data = [line.split("\t") for line in text.splitlines()]
        if (row0 + len(data)) > self.rowCount():
            self.setRowCount(row0 + len(data))
        if data and (col0 + len(data[0])) > self.columnCount():
            self.setColumnCount(col0 + len(data[0]))
        for r, line in enumerate(data):
            for c, cell in enumerate(line):
                try:
                    self.item(row0 + r, col0 + c).setText(str(cell))
                except AttributeError:
                    self.setItem(row0 + r, col0 + c, QtW.QTableWidgetItem(str(cell)))

        # select what was just pasted
        selrange = QtW.QTableWidgetSelectionRange(row0, col0, row0 + r, col0 + c)
        self.clearSelection()
        self.setRangeSelected(selrange, True)

    def _delete_selection(self):
        if self._read_only:
            return

        for item in self.selectedItems():
            try:
                item.setText("")
            except AttributeError:
                pass

    def keyPressEvent(self, e: QKeyEvent):
        if e.modifiers() & Qt.ControlModifier and e.key() == Qt.Key_C:
            return self._copy_to_clipboard()
        if e.modifiers() & Qt.ControlModifier and e.key() == Qt.Key_V:
            return self._paste_from_clipboard()
        if e.modifiers() & Qt.ControlModifier and e.key() == Qt.Key_X:
            self._copy_to_clipboard()
            return self._delete_selection()
        if e.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            return self._delete_selection()
        return super().keyPressEvent(e)


class Table(QBaseWidget, _protocols.TableWidgetProtocol):
    _qwidget: _QTableExtended
    _DATA_ROLE: int = 255
    _EDITABLE = QtW.QTableWidget.EditKeyPressed | QtW.QTableWidget.DoubleClicked
    _READ_ONLY = QtW.QTableWidget.NoEditTriggers

    def __init__(self, **kwargs):
        super().__init__(_QTableExtended, **kwargs)
        header = self._qwidget.horizontalHeader()
        # avoid strange AttributeError on CI
        if hasattr(header, "setSectionResizeMode"):
            header.setSectionResizeMode(QtW.QHeaderView.Stretch)
        # self._qwidget.horizontalHeader().setSectionsMovable(True)  # tricky!!
        header.setSectionResizeMode(QtW.QHeaderView.Interactive)
        self._qwidget.itemChanged.connect(self._update_item_data_with_text)

    def _mgui_set_read_only(self, value: bool) -> None:
        value = bool(value)
        self._qwidget._read_only = value
        if value:
            self._qwidget.setEditTriggers(self._READ_ONLY)
        else:
            self._qwidget.setEditTriggers(self._EDITABLE)

    def _mgui_get_read_only(self) -> bool:
        return self._qwidget._read_only

    def _update_item_data_with_text(self, item: QtW.QTableWidgetItem):
        with _signals_blocked(self._qwidget):
            item.setData(self._DATA_ROLE, _maybefloat(item.text()))

    def _mgui_set_row_count(self, nrows: int) -> None:
        """Set the number of rows in the table. (Create/delete as needed)."""
        self._qwidget.setRowCount(nrows)

    def _mgui_set_column_count(self, ncols: int) -> None:
        """Set the number of columns in the table. (Create/delete as needed)."""
        self._qwidget.setColumnCount(ncols)

    def _mgui_get_column_count(self) -> int:
        return self._qwidget.columnCount()

    def _mgui_get_row_count(self) -> int:
        return self._qwidget.rowCount()

    def _mgui_remove_row(self, row: int) -> None:
        self._qwidget.removeRow(row)

    def _mgui_remove_column(self, column: int) -> None:
        self._qwidget.removeColumn(column)

    def _mgui_get_cell(self, row: int, col: int) -> Any:
        """Get current value of the widget."""
        item = self._qwidget.item(row, col)
        if item:
            return item.data(self._DATA_ROLE)
        widget = self._qwidget.cellWidget(row, col)
        if widget:
            return getattr(widget, "_magic_widget", widget)

    def _mgui_set_cell(self, row: int, col: int, value: Any) -> None:
        """Set current value of the widget."""
        if value is None:
            self._qwidget.setItem(row, col, None)
            self._qwidget.removeCellWidget(row, col)
            return
        if isinstance(value, Widget):
            self._qwidget.setCellWidget(row, col, value.native)
            return
        item = QtW.QTableWidgetItem(str(value))
        item.setData(self._DATA_ROLE, value)
        self._qwidget.setItem(row, col, item)

    def _mgui_get_row_headers(self) -> tuple:
        """Get current row headers of the widget."""
        # ... 'PySide2.QtWidgets.QTableWidgetItem' object has no attribute 'visualIndex'
        # on some linux... so removing the visualIndex() for row headers... this means
        # we can't enable row drag/drop without fixing this
        indices = range(self._qwidget.rowCount())
        items = (self._qwidget.verticalHeaderItem(i) for i in indices)
        headers = (item.text() for item in items if item)
        return tuple(_maybefloat(x) for x in headers)

    def _mgui_set_row_headers(self, headers: Sequence) -> None:
        """Set current row headers of the widget."""
        self._qwidget.setVerticalHeaderLabels(tuple(map(str, headers)))

    def _mgui_get_column_headers(self) -> tuple:
        """Get current column headers of the widget."""
        horiz_header = self._qwidget.horizontalHeader()
        ncols = self._qwidget.columnCount()
        # visual index allows for column drag/drop, though it's currently not enabled.
        indices = (horiz_header.visualIndex(i) for i in range(ncols))
        items = (self._qwidget.horizontalHeaderItem(i) for i in indices)
        headers = (item.text() for item in items if item)
        return tuple(_maybefloat(x) for x in headers)

    def _mgui_set_column_headers(self, headers: Sequence) -> None:
        """Set current column headers of the widget."""
        self._qwidget.setHorizontalHeaderLabels(tuple(map(str, headers)))

    def _mgui_bind_row_headers_change_callback(self, callback) -> None:
        """Bind callback to row headers change event."""
        raise NotImplementedError()

    def _mgui_bind_column_headers_change_callback(self, callback) -> None:
        """Bind callback to column headers change event."""
        raise NotImplementedError()

    def _mgui_bind_change_callback(self, callback):
        """Bind callback to event of changing any cell."""
        self._qwidget.itemChanged.connect(partial(self._item_callback, callback))

    def _item_callback(self, callback, item: QtW.QTableWidgetItem):
        col_head = item.tableWidget().horizontalHeaderItem(item.column())
        col_head = col_head.text() if col_head is not None else ""
        row_head = item.tableWidget().verticalHeaderItem(item.row())
        row_head = row_head.text() if row_head is not None else ""
        data = {
            "data": item.data(self._DATA_ROLE),
            "row": item.row(),
            "column": item.column(),
            "column_header": col_head,
            "row_header": row_head,
        }
        callback(data)

    # These are only here to implement the ValueWidget interface... but in this one
    # case, all of the get/set value logic happens in magicgui.widgets.Table
    # calling Table._mgui_set_cell and Table._mgui_get_cell instead
    def _mgui_get_value(self):
        pass

    def _mgui_set_value(self):
        pass


class _ItemDelegate(QtW.QStyledItemDelegate):
    """Displays table widget items with properly formatted numbers."""

    def displayText(self, value, locale):
        return super().displayText(_format_number(value, 4), locale)


def _format_number(text: str, ndigits: int = 4) -> str:
    """convert string to int or float if possible"""
    try:
        value: int | float | None = int(text)
    except ValueError:
        try:
            value = float(text)
        except ValueError:
            value = None

    if isinstance(value, (int, float)):
        if 0.1 <= abs(value) < 10 ** (ndigits + 1) or value == 0:
            text = str(value) if isinstance(value, int) else f"{value:.{ndigits}f}"
        else:
            text = f"{value:.{ndigits-1}e}"

    return text
