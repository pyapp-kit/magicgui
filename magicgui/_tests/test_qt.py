#!/usr/bin/env python

"""Tests for `magicgui._qt` module."""

import datetime
from enum import Enum
from pathlib import Path, PosixPath, WindowsPath
from typing import List, Sequence, Tuple

import pytest
from qtpy import QtCore, API_NAME
from qtpy import QtWidgets as QtW

from magicgui import _qt, event_loop


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
        _qt.widgets.QDataComboBox,
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
        _qt.widgets.QDoubleSlider,
        _qt.widgets.MagicFileDialog,
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
    slider = _qt.widgets.QDoubleSlider()
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


def test_make_widget_magicfiledialog(qtbot):
    """Test MagicFileDialog creation with kwargs 'mode' and 'filter'."""
    w = _qt.make_widget(
        _qt.widgets.MagicFileDialog,
        "magicfiledialog",
        mode="r",
        filter="Images (*.tif *.tiff)",
    )
    assert w.mode == _qt.FileDialogMode.EXISTING_FILE
    assert w.filter == "Images (*.tif *.tiff)"


def test_datetimeedit(qtbot):
    """Test the datetime getter."""
    getter, setter, onchange = _qt.getter_setter_onchange(QtW.QDateTimeEdit())
    assert isinstance(getter(), datetime.datetime)


def test_set_categorical(qtbot):
    """Test the categorical setter."""
    W = _qt.get_categorical_widget()
    w = W()
    _qt.set_categorical_choices(w, (("a", 1), ("b", 2)))
    assert [w.itemText(i) for i in range(w.count())] == ["a", "b"]
    _qt.set_categorical_choices(w, (("a", 1), ("c", 3)))
    assert [w.itemText(i) for i in range(w.count())] == ["a", "c"]


def test_magicfiledialog(qtbot):
    """Test the MagicFileDialog class."""
    filewidget = _qt.widgets.MagicFileDialog()

    # check default values
    assert filewidget.get_path() == Path(".")
    assert filewidget.mode == _qt.FileDialogMode.EXISTING_FILE

    # set the mode
    filewidget.mode = _qt.FileDialogMode.EXISTING_FILES  # Enum input
    assert filewidget.mode == _qt.FileDialogMode.EXISTING_FILES
    filewidget.mode = "oPtioNal_FiLe"  # improper capitalization
    assert filewidget.mode == _qt.FileDialogMode.OPTIONAL_FILE
    filewidget.mode = "EXISTING_DIRECTORY"  # string input
    assert filewidget.mode == _qt.FileDialogMode.EXISTING_DIRECTORY
    with pytest.raises(ValueError):
        filewidget.mode = 123  # invalid mode
        filewidget.mode = "invalid_string"

    # set the path
    filewidget.set_path("my/example/path/")
    assert filewidget.get_path() == Path("my/example/path/")

    filewidget.mode = _qt.FileDialogMode.EXISTING_FILES
    filewidget.set_path(["path/one.txt", "path/two.txt"])
    assert filewidget.get_path() == (Path("path/one.txt"), Path("path/two.txt"))
    filewidget.set_path(["path/3.txt, path/4.txt"])
    assert filewidget.get_path() == (Path("path/3.txt"), Path("path/4.txt"))

    with pytest.raises(TypeError):
        filewidget.set_path(123)  # invalid type, only str/Path accepted


@pytest.mark.skipif("sys.platform == 'darwin'")  # dialog box hangs on Mac
@pytest.mark.parametrize("mode", ["r", "EXISTING_DIRECTORY"])
def test_magicfiledialog_opens_chooser(qtbot, mode):
    """Test the choose button opens a popup file dialog."""
    filewidget = _qt.widgets.MagicFileDialog()
    filewidget.set_path((".",))  # set_path with tuple for better code coverage
    filewidget.mode = mode

    def handle_dialog():
        popup_filedialog = next(
            child
            for child in filewidget.children()
            if isinstance(child, QtW.QFileDialog)
        )
        assert isinstance(popup_filedialog, QtW.QFileDialog)
        popup_filedialog.reject()

    QtCore.QTimer().singleShot(400, handle_dialog)
    filewidget._on_choose_clicked()


@pytest.mark.parametrize("containertype", [None, Tuple, List, Sequence])
@pytest.mark.parametrize("pathtype", [PosixPath, WindowsPath, Path])
def test_magifiledialog_type2widget(containertype, pathtype):
    """Test we get a MagicFileDialog from a various Path types."""
    if containertype is not None:
        Wdg = _qt.type2widget(containertype[pathtype])
        assert Wdg == _qt.widgets.MagicFilesDialog
        assert Wdg().mode == _qt.FileDialogMode.EXISTING_FILES
    else:
        assert _qt.type2widget(pathtype) == _qt.widgets.MagicFileDialog


def test_literal_eval_edit():
    """Test the literal eval widget converts text to python objects."""
    widget = _qt.widgets.LiteralEvalEdit()
    widget.setText("(1, 0)")
    assert widget.text() == (1, 0)
