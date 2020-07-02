# -*- coding: utf-8 -*-
"""Widgets and type-to-widget conversion for the Qt backend."""

import os
import sys
from contextlib import contextmanager
import datetime
from enum import Enum, EnumMeta
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    Union,
)

from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QAbstractButton,
    QAbstractSlider,
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from qtpy.QtCore import SignalInstance as SignalInstanceType
except ImportError:
    from qtpy.QtCore import pyqtBoundSignal as SignalInstanceType


@contextmanager
def event_loop():
    """Start a Qt event loop in which to run the application."""
    app = QApplication.instance() or QApplication(sys.argv)
    yield
    app.exec_()


class WidgetType(QWidget):
    """Widget that reports when its parent has changed."""

    parentChanged = Signal()

    def setParent(self, parent):
        """Set parent widget and emit signal."""
        super().setParent(parent)
        self.parentChanged.emit()


ButtonType = QPushButton
SignalType = Signal


class GetSetOnChange(NamedTuple):
    """Named tuple for a (getter, setter, onchange) tuple."""

    getter: Callable[[], Any]
    setter: Callable[[Any], None]
    onchange: SignalInstanceType


class HelpfulEnum(EnumMeta):
    """Metaclass that shows the available options on KeyError."""

    def __getitem__(self, name: str):
        """Get enum by name, or raise helpful KeyError."""
        try:
            return super().__getitem__(name)
        except (TypeError, KeyError):
            options = set(self.__members__.keys())
            raise KeyError(
                f"'{name}' is not a valid Layout. Options include: {options}"
            )


class Layout(Enum, metaclass=HelpfulEnum):
    """QLayout options."""

    vertical = QVBoxLayout
    horizontal = QHBoxLayout
    grid = QGridLayout
    form = QFormLayout

    @staticmethod
    def addWidget(layout: QLayout, widget: QWidget, label: str = ""):
        """Add widget to arbitrary layout with optional label."""
        if isinstance(layout, QFormLayout):
            return layout.addRow(label, widget)
        elif isinstance(layout, (QHBoxLayout, QVBoxLayout)):
            if label:
                label_widget = QLabel(label)
                label_widget.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
                layout.addWidget(label_widget)
            return layout.addWidget(widget)

    @staticmethod
    def insertWidget(layout: QLayout, position: int, widget: QWidget, label: str = ""):
        """Add widget to arbitrary layout at position, with optional label."""
        if position < 0:
            position = layout.count() + position + 1
        if isinstance(layout, QFormLayout):
            layout.insertRow(position, label, widget)
        else:
            layout.insertWidget(position, widget)
            if label:
                label_widget = QLabel(label)
                label_widget.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
                layout.insertWidget(position, label_widget)


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


def type2widget(type_: type) -> Optional[Type[WidgetType]]:
    """Convert an python type to Qt widget.

    Parameters
    ----------
    type_ : type
        The argument type.

    Returns
    -------
    WidgetType: Type[WidgetType]
        A WidgetType Class that can be used for arg_type ``type_``.
    """
    simple: Dict[type, Type[WidgetType]] = {
        bool: QCheckBox,
        int: QSpinBox,
        float: QDoubleSpinBox,
        str: QLineEdit,
        Path: MagicFileDialog,
        datetime.datetime: QDateTimeEdit,
        type(None): QLineEdit,
    }
    if type_ in simple:
        return simple[type_]
    elif isinstance(type_, EnumMeta):
        return QDataComboBox
    else:
        for key in simple.keys():
            if issubclass(type_, key):
                return simple[key]
    return None


def getter_setter_onchange(widget: WidgetType) -> GetSetOnChange:
    """Return a GetSetOnChange tuple for widgets of class ``WidgetType``.

    Parameters
    ----------
    widget : WidgetType
        A widget class in Qt

    Returns
    -------
    GetSetOnChange : tuple
        (getter, setter, onchange) functions for this widget class.

    Raises
    ------
    ValueError
        If the widget class is unrecognzed.
    """
    if isinstance(widget, QComboBox):

        def getter():
            return widget.itemData(widget.currentIndex())

        onchange = (
            widget.currentDataChanged
            if hasattr(widget, "currentDataChanged")
            else widget.currentIndexChanged
        )
        return GetSetOnChange(getter, widget.setCurrentIndex, onchange)
    elif isinstance(widget, QStatusBar):
        return GetSetOnChange(
            widget.currentMessage, widget.showMessage, widget.messageChanged
        )
    elif isinstance(widget, QLineEdit):
        return GetSetOnChange(
            widget.text, lambda x: widget.setText(str(x)), widget.textChanged
        )
    elif isinstance(widget, (QAbstractButton, QGroupBox)):
        return GetSetOnChange(widget.isChecked, widget.setChecked, widget.toggled)
    elif isinstance(widget, QDateTimeEdit):

        def getter():
            try:
                return widget.dateTime().toPython()
            except TypeError:
                return widget.dateTime().toPyDateTime()

        return GetSetOnChange(getter, widget.setDateTime, widget.dateTimeChanged)
    elif isinstance(widget, (QAbstractSpinBox, QAbstractSlider)):
        return GetSetOnChange(widget.value, widget.setValue, widget.valueChanged)
    elif isinstance(widget, QTabWidget):
        return GetSetOnChange(
            widget.currentIndex, widget.setCurrentIndex, widget.currentChanged
        )
    elif isinstance(widget, QSplitter):
        return GetSetOnChange(widget.sizes, widget.setSizes, widget.splitterMoved)
    elif isinstance(widget, MagicFileDialog):
        return GetSetOnChange(
            widget.get_path, widget.set_path, widget.line_edit.textChanged
        )
    raise ValueError(f"Unrecognized widget Type: {widget}")


def set_categorical_choices(widget: WidgetType, choices: Iterable[Tuple[str, Any]]):
    """Set current items in categorical type ``widget`` to ``choices``."""
    names = [x[0] for x in choices]
    for i in range(widget.count()):
        if widget.itemText(i) not in names:
            widget.removeItem(i)
    for name, data in choices:
        if widget.findText(name) == -1:
            widget.addItem(name, data)


def get_categorical_widget():
    """Get the categorical widget type for Qt."""
    return QDataComboBox


def is_categorical(widget: WidgetType):
    """Return True if ``widget`` is a categorical widget."""
    return isinstance(widget, QComboBox)


def get_categorical_index(widget: WidgetType, value: Any):
    """Find the index of ``value`` in categorical-type ``widget``."""
    return next(i for i in range(widget.count()) if widget.itemData(i) == value)


def make_widget(
    WidgetType: Type[WidgetType],
    name: Optional[str] = None,
    parent: WidgetType = None,
    **kwargs,
) -> WidgetType:
    """Instantiate a new widget of type ``WidgetType``.

    This function allows for any ``widget.set<AttrName>()`` setter to be called by
    providing the corresponding ``attrName: value`` as a key/value in pair in
    ``**kwargs``.

    Parameters
    ----------
    WidgetType : Type[WidgetType]
        The widget class to create.
    name : str, optional
        Name of the widget.  If provided, will be set as ObjectName. by default None
    parent : WidgetType, optional
        Optional parent widget instance, by default None
    **kwargs : dict
        For each ``key`` in ``kwargs``, if there is a setter method on the instantiated
        widget called ``set<key>``, it will called with ``kwargs[key]``.  Note, the
        first letter of ``key`` needn't be capitalized.

    Returns
    -------
    widget : WidgetType
        The newly instantiated widget
    """
    widget = WidgetType(parent=parent)
    if name:
        widget.setObjectName(name)
    for key, val in kwargs.items():
        setter = getattr(widget, f"set{key[0].upper() + key[1:]}", None)
        if setter:
            setter(val)

    if isinstance(widget, MagicFileDialog):
        if "mode" in kwargs:
            widget.mode = kwargs["mode"]
        if "filter" in kwargs:
            widget.filter = kwargs["filter"]
    return widget


# ############ WIDGETS ############ #


class QDoubleSlider(QSlider):
    """A Slider Widget that can handle float values."""

    PRECISION = 1000

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent=parent)
        self.setMaximum(10)

    def value(self):
        """Get the slider value and convert to float."""
        return super().value() / self.PRECISION

    def setValue(self, value):
        """Set integer slider position from float ``value``."""
        super().setValue(value * self.PRECISION)

    def setMaximum(self, value):
        """Set maximum position of slider in float units."""
        super().setMaximum(value * self.PRECISION)


class FileDialogMode(Enum):
    """FileDialog mode options.

    EXISTING_FILE - returns one existing file.
    EXISTING_FILES - return one or more existing files.
    OPTIONAL_FILE - return one file name that does not have to exist.
    EXISTING_DIRECTORY - returns one existing directory.
    R - read mode, returns one or more existing files.
        Alias of EXISTING_FILES.
    W - write mode, returns one file name that does not have to exist.
        Alias of OPTIONAL_FILE.
    """

    EXISTING_FILE = "getOpenFileName"
    EXISTING_FILES = "getOpenFileNames"
    OPTIONAL_FILE = "getSaveFileName"
    EXISTING_DIRECTORY = "getExistingDirectory"
    # Aliases
    R = "getOpenFileNames"
    W = "getSaveFileName"


class MagicFileDialog(QWidget):
    """A LineEdit widget with a QFileDialog button."""

    def __init__(
        self,
        parent=None,
        mode: Union[FileDialogMode, str] = FileDialogMode.OPTIONAL_FILE,
        filter: str = "",
    ):
        super().__init__(parent)
        self.line_edit = QLineEdit(self)
        self.choose_btn = QPushButton("Choose file", self)
        self.choose_btn.clicked.connect(self._on_choose_clicked)
        self.mode = mode
        self.filter: str = filter
        layout = QHBoxLayout(self)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.choose_btn)

    def _help_text(self):
        if self.mode is FileDialogMode.EXISTING_DIRECTORY:
            return "Choose directory"
        else:
            return "Select file" + ("s" if self.mode.name.endswith("S") else "")

    @property
    def mode(self):
        """Mode for the FileDialog."""
        return self._mode

    @mode.setter
    def mode(self, value: Union[FileDialogMode, str]):
        mode: Union[FileDialogMode, str] = value
        if isinstance(value, str):
            try:
                mode = FileDialogMode(value)
            except ValueError:
                try:
                    mode = FileDialogMode[value.upper()]
                except KeyError:
                    pass
        if not isinstance(mode, FileDialogMode):
            raise ValueError(
                f"{mode!r} is not a valid FileDialogMode. "
                f"Options include {set(i.name.lower() for i in FileDialogMode)}"
            )
        self._mode = mode
        self.choose_btn.setText(self._help_text())

    def _on_choose_clicked(self):
        show_dialog = getattr(QFileDialog, self.mode.value)
        start_path = self.get_path()
        if isinstance(start_path, tuple):
            start_path = start_path[0]
        start_path = os.fspath(os.path.abspath(os.path.expanduser(start_path)))
        caption = self._help_text()
        if self.mode is FileDialogMode.EXISTING_DIRECTORY:
            result = show_dialog(self, caption, start_path)
        else:
            result, _ = show_dialog(self, caption, start_path, self.filter)
        if result:
            self.set_path(result)

    def get_path(self) -> Union[Tuple[Path, ...], Path]:
        """Get current file path."""
        text = self.line_edit.text()
        if self.mode is FileDialogMode.EXISTING_FILES:
            return tuple(Path(p) for p in text.split(", "))
        return Path(text)

    def set_path(self, value: Union[List[str], Tuple[str, ...], str, Path]):
        """Set current file path."""
        if isinstance(value, (list, tuple)):
            value = ", ".join([os.fspath(p) for p in value])
        if not isinstance(value, (str, Path)):
            raise TypeError(
                f"value must be a string, or list/tuple of strings, got {type(value)}"
            )
        self.line_edit.setText(str(value))
