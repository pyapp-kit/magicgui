# -*- coding: utf-8 -*-
"""Widgets and type-to-widget conversion for the Qt backend."""
from ._qt import event_loop, getter_setter_onchange, make_widget, type2widget
from .categorical import (
    get_categorical_index,
    get_categorical_widget,
    is_categorical,
    set_categorical_choices,
)
from .constants import FileDialogMode, Layout
from .types import ButtonType, SignalType
from .widgets import LiteralEvalEdit, WidgetType

FALLBACK_WIDGET = LiteralEvalEdit

__all__ = [
    "ButtonType",
    "FileDialogMode",
    "Layout",
    "SignalType",
    "WidgetType",
    "event_loop",
    "get_categorical_index",
    "get_categorical_widget",
    "getter_setter_onchange",
    "is_categorical",
    "make_widget",
    "set_categorical_choices",
    "type2widget",
    "FALLBACK_WIDGET",
]
