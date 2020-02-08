#!/usr/bin/env python

"""Tests for `magicgui` package."""

from enum import Enum

import pytest
from qtpy import QtWidgets as QtW

from magicgui import magicgui


def test_magicgui(qtbot):
    @magicgui
    def func(a: str = "string", b: int = 3, c=7.1) -> str:
        return "works"

    widget = func.Gui()
    assert func() == "works"
    assert widget.a == "string"
    assert widget.b == 3
    assert widget.c == 7.1
    assert isinstance(widget.a_widget, QtW.QLineEdit)
    assert isinstance(widget.b_widget, QtW.QSpinBox)
    assert isinstance(widget.c_widget, QtW.QDoubleSpinBox)

    widget.show()
    assert widget.isVisible()


def test_dropdown_list_from_enum(qtbot):
    class RI(Enum):
        Oil = 1.515
        Water = 1.33
        Air = 1.0

    @magicgui
    def func(arg: RI = RI.Water):
        ...

    widget = func.Gui()
    assert isinstance(widget.arg_widget, QtW.QComboBox)
    items = [widget.arg_widget.itemText(i) for i in range(widget.arg_widget.count())]
    assert items == ["Oil", "Water", "Air"]


def test_dropdown_list_from_str(qtbot):
    CHOICES = ["Oil", "Water", "Air"]

    @magicgui(arg={"choices": CHOICES})
    def func(arg="Water"):
        ...

    widget = func.Gui()
    assert isinstance(widget.arg_widget, QtW.QComboBox)
    items = [widget.arg_widget.itemText(i) for i in range(widget.arg_widget.count())]
    assert items == CHOICES

    # the default value must be in the list
    @magicgui(arg={"choices": ["Oil", "Water", "Air"]})
    def func(arg="Silicone"):
        ...

    with pytest.raises(ValueError):
        widget = func.Gui()
