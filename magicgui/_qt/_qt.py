# -*- coding: utf-8 -*-
"""Widgets and type-to-widget conversion for the Qt backend."""

import datetime
import inspect
import sys
from collections import abc
from contextlib import contextmanager
from enum import EnumMeta
from pathlib import Path
from typing import Any, Callable, Dict, NamedTuple, Optional, Type, Union

from qtpy.QtWidgets import (
    QAbstractButton,
    QAbstractSlider,
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDoubleSpinBox,
    QGroupBox,
    QLineEdit,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
)

from .widgets import MagicFileDialog, MagicFilesDialog, QDataComboBox, WidgetType

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


def type2widget(type_: Union[type]) -> Optional[Type[WidgetType]]:
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
    #
    if hasattr(type_, "__origin__") and hasattr(type_, "__args__"):
        orig = type_.__origin__  # type: ignore
        arg = type_.__args__[0] if len(type_.__args__) else None  # type: ignore
        if inspect.isclass(orig) and issubclass(orig, abc.Sequence):
            if inspect.isclass(arg) and issubclass(arg, Path):
                return MagicFilesDialog

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
            if inspect.isclass(type_) and issubclass(type_, key):
                return simple[key]
    return None


class GetSetOnChange(NamedTuple):
    """Named tuple for a (getter, setter, onchange) tuple."""

    getter: Callable[[], Any]
    setter: Callable[[Any], None]
    onchange: SignalInstanceType


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
