#!/usr/bin/env python

"""Tests for `magicgui` package."""

from magicgui import magicgui
from qtpy.QtWidgets import QLineEdit, QDoubleSpinBox, QSpinBox


def test_magicgui(qtbot):
    @magicgui
    def test_function(a: str = "string", b: int = 3, c=7.1) -> str:
        """my docs"""
        return "works"

    widget = test_function.Gui()
    assert test_function() == "works"
    assert widget.a == "string"
    assert widget.b == 3
    assert widget.c == 7.1
    assert isinstance(widget.a_widget, QLineEdit)
    assert isinstance(widget.b_widget, QSpinBox)
    assert isinstance(widget.c_widget, QDoubleSpinBox)

    widget.show()
    assert widget.isVisible()
