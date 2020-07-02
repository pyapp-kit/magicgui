#!/usr/bin/env python

"""Tests for `magicgui._qt` module."""

import datetime
from enum import Enum
from pathlib import Path, PosixPath, WindowsPath

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
        _qt.MagicFileDialog,
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


def test_make_widget_magicfiledialog(qtbot):
    """Test MagicFileDialog creation with kwargs 'mode' and 'filter'."""
    w = _qt.make_widget(_qt.MagicFileDialog, "magicfiledialog",
                        mode="r",
                        filter="Images (*.tif *.tiff)")
    assert w.mode == _qt.FileDialogMode.EXISTING_FILES
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
    filewidget = _qt.MagicFileDialog()

    # check default values
    assert filewidget.get_path() == Path('.')
    assert filewidget.mode == _qt.FileDialogMode.OPTIONAL_FILE

    # set the mode
    filewidget.mode = _qt.FileDialogMode.EXISTING_FILES  # Enum input
    assert filewidget.mode == _qt.FileDialogMode.EXISTING_FILES
    filewidget.mode = "oPtioNal_FiLe"  # improper capitalization
    assert filewidget.mode == _qt.FileDialogMode.OPTIONAL_FILE
    filewidget.mode = "EXISTING_DIRECTORY"  # string input
    assert filewidget.mode == _qt.FileDialogMode.EXISTING_DIRECTORY
    with pytest.raises(ValueError):
        filewidget.mode = 123  # invalid mode

    # set the path
    filewidget.set_path('my/example/path/')
    assert filewidget.get_path() == Path('my/example/path/')

    filewidget.mode = _qt.FileDialogMode.EXISTING_FILES
    filewidget.set_path(['path/one.txt', 'path/two.txt'])
    assert filewidget.get_path() == (Path('path/one.txt'), Path('path/two.txt'))
    filewidget.set_path(['path/3.txt, path/4.txt'])
    assert filewidget.get_path() == (Path('path/3.txt'), Path('path/4.txt'))

    with pytest.raises(TypeError):
        filewidget.set_path(123)  # invalid type, only str/Path accepted


@pytest.mark.skipif("sys.platform == 'darwin'")  # dialog box hangs on Mac
@pytest.mark.parametrize("mode", [
    ('r'),  # existing file
    ('EXISTING_DIRECTORY'),
])
def test_magicfiledialog_opens_chooser(qtbot, mode):
    """Test the choose button opens a popup file dialog."""
    filewidget = _qt.MagicFileDialog()
    filewidget.set_path(('.',))  # set_path with tuple for better code coverage
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


@pytest.mark.skipif("sys.platform == 'windows'")  # Windows only test
def test_windows_magicfiledialog(qtbot):
    w = _qt.type2widget(WindowsPath)
    assert w is not None
    assert _qt.MagicFileDialog in w.mro()  # since type(w) = sip.wrappertype


@pytest.mark.skipif("sys.platform != 'windows'")  # Linux and Mac test
def test_linux_mac_magifiledialog(qtbot):
    w = _qt.type2widget(PosixPath)
    assert w is not None
    assert _qt.MagicFileDialog in w.mro()  # since type(w) = sip.wrappertype
