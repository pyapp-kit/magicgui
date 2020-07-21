"""Stuff for handling categorical data."""
from typing import Iterable, Tuple, Any

from qtpy.QtWidgets import QComboBox

from .widgets import QDataComboBox, WidgetType


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
