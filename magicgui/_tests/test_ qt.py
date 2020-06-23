#!/usr/bin/env python

"""Tests for `magicgui._qt` module."""

from enum import Enum

import pytest
from qtpy import QtCore
from qtpy import QtWidgets as QtW

from magicgui import _qt, event_loop


def test_event():
    """Test that the event loop makes a Qt app."""
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
        _qt.QDataComboBox,
        QtW.QComboBox,
        QtW.QStatusBar,
        QtW.QLineEdit,
        QtW.QPushButton,
        QtW.QGroupBox,
        QtW.QDateTimeEdit,
        QtW.QSpinBox,
        QtW.QDoubleSpinBox,
        QtW.QAbstractSlider,
        QtW.QTabWidget,
        QtW.QSplitter,
        QtW.QSlider,
        _qt.QDoubleSlider,
    ],
)
def test_get_set_change(qtbot, WidgetClass):
    """Test that we can retrieve getters, setters, and signals for most Widgets."""
    w = WidgetClass()
    assert _qt.getter_setter_onchange(w)

    class Random:
        ...

    with pytest.raises(ValueError):
        _qt.getter_setter_onchange(Random())  # type: ignore


def test_double_slider(qtbot):
    """Test basic slider functionality."""
    slider = _qt.QDoubleSlider()
    assert slider.value() == 0
    slider.setValue(5.5)
    assert slider.value() == 5.5
    assert QtW.QSlider.value(slider) == 5.5 * slider.PRECISION


@pytest.mark.parametrize("type", [Enum, int, float, str, list, dict, set])
def test_type2widget(type):
    """Test that type2widget returns successfully."""
    _qt.type2widget(type)


def test_setters(qtbot):
    """Test that make_widget accepts any arg that has a set<arg> method."""
    w = _qt.make_widget(QtW.QDoubleSpinBox, "spinbox", minimum=2, Maximum=10)
    assert w.minimum() == 2
    assert w.maximum() == 10


def test_set_categorical(qtbot):
    """Test the categorical setter."""
    W = _qt.get_categorical_widget()
    w = W()
    _qt.set_categorical_choices(w, (("a", 1), ("b", 2)))
    assert [w.itemText(i) for i in range(w.count())] == ["a", "b"]
    _qt.set_categorical_choices(w, (("a", 1), ("c", 3)))
    assert [w.itemText(i) for i in range(w.count())] == ["a", "c"]
