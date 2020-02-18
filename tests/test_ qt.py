#!/usr/bin/env python

"""Tests for `magicgui._qt` module."""

import pytest
from qtpy import QtWidgets as QtW

from magicgui import _qt


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
