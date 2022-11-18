#!/usr/bin/env python

"""Tests for `magicgui._qt` module."""


import pytest
from qtpy import API_NAME, QtCore
from qtpy import QtWidgets as QtW

from magicgui import event_loop, widgets


@pytest.mark.skipif("PyQt" in API_NAME, reason="Couldn't delete app on PyQt")
def test_event():
    """Test that the event loop makes a Qt app."""
    if QtW.QApplication.instance():
        if API_NAME == "PySide2":
            __import__("shiboken2").delete(QtW.QApplication.instance())
        elif API_NAME == "PySide6":
            __import__("shiboken6").delete(QtW.QApplication.instance())
        else:
            raise AssertionError(f"known API name: {API_NAME}")
    assert not QtW.QApplication.instance()
    with event_loop():
        app = QtW.QApplication.instance()
        assert app
        timer = QtCore.QTimer()
        timer.timeout.connect(lambda: app.exit())
        timer.start(100)


@pytest.mark.parametrize(
    "WidgetClass",
    [
        widgets.ComboBox,
        widgets.LineEdit,
        widgets.PushButton,
        widgets.DateTimeEdit,
        widgets.SpinBox,
        widgets.FloatSpinBox,
        widgets.Slider,
        widgets.FloatSlider,
        widgets.FileEdit,
    ],
)
def test_get_set_change(WidgetClass):
    """Test that we can retrieve getters, setters, and signals for most Widgets."""
    _ = WidgetClass()
