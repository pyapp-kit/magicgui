#!/usr/bin/env python

"""Tests for `magicgui._qt` module."""


import pytest
from qtpy import API_NAME, QtCore
from qtpy import QtWidgets as QtW

from magicgui import event_loop, widgets


@pytest.mark.skipif(API_NAME == "PyQt5", reason="Couldn't delete app on PyQt")
def test_event():
    """Test that the event loop makes a Qt app."""
    if QtW.QApplication.instance():
        import shiboken2

        shiboken2.delete(QtW.QApplication.instance())
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
