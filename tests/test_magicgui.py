#!/usr/bin/env python

"""Tests for `magicgui` package."""

from enum import Enum

import pytest
from inspect import signature
from qtpy import QtWidgets as QtW
from qtpy.QtCore import Qt

from magicgui import magicgui


@pytest.fixture
def magic_func():
    """Test function decorated by magicgui."""

    @magicgui(call_button="my_button", auto_call=True)
    def func(a: str = "string", b: int = 3, c=7.1) -> str:
        return "works"

    return func


@pytest.fixture
def magic_widget(qtbot, magic_func):
    """Test instantiated widget."""
    return magic_func.Gui()


def test_magicgui(magic_widget):
    """Test basic magicgui functionality."""
    assert magic_widget.func() == "works"
    assert magic_widget.a == "string"
    assert magic_widget.b == 3
    assert magic_widget.c == 7.1
    assert isinstance(magic_widget.get_widget("a"), QtW.QLineEdit)
    assert isinstance(magic_widget.get_widget("b"), QtW.QSpinBox)
    assert isinstance(magic_widget.get_widget("c"), QtW.QDoubleSpinBox)

    magic_widget.show()
    assert magic_widget.isVisible()

    # we can delete widgets
    del magic_widget.a
    with pytest.raises(AttributeError):
        getattr(magic_widget, "a")

    # they disappear from the layout
    widg = magic_widget.get_widget("a")
    assert magic_widget.layout().indexOf(widg) == -1


def test_call_button(magic_widget):
    """Test that the call button has been added."""
    assert hasattr(magic_widget, "call_button")
    assert isinstance(magic_widget.call_button, QtW.QPushButton)


def test_auto_call(qtbot, magic_func):
    """Test that changing a parameter calls the function."""
    magic_widget = magic_func.Gui()

    # changing the widget parameter calls the function
    with qtbot.waitSignal(magic_func.called, timeout=1000):
        magic_widget.b = 6

    # changing the gui calls the function
    with qtbot.waitSignal(magic_func.called, timeout=1000):
        qtbot.keyClick(magic_widget.a_widget, Qt.Key_A, Qt.ControlModifier)
        qtbot.keyClick(magic_widget.a_widget, Qt.Key_Delete)


def test_dropdown_list_from_enum(qtbot):
    """Test that enums properly populate the dropdown menu with options."""

    class Medium(Enum):
        Glass = 1.520
        Oil = 1.515
        Water = 1.333
        Air = 1.0003

    @magicgui
    def func(arg: Medium = Medium.Water):
        ...

    widget = func.Gui()
    assert widget.arg == Medium.Water
    assert isinstance(widget.arg_widget, QtW.QComboBox)
    items = [widget.arg_widget.itemText(i) for i in range(widget.arg_widget.count())]
    assert items == Medium._member_names_


def test_dropdown_list_from_str(qtbot):
    """Test that providing the 'choices' argument with a list of strings works."""
    CHOICES = ["Oil", "Water", "Air"]

    @magicgui(arg={"choices": CHOICES})
    def func(arg="Water"):
        ...

    widget = func.Gui()
    assert widget.arg == "Water"
    assert isinstance(widget.arg_widget, QtW.QComboBox)
    items = [widget.arg_widget.itemText(i) for i in range(widget.arg_widget.count())]
    assert items == CHOICES

    # the default value must be in the list
    @magicgui(arg={"choices": ["Oil", "Water", "Air"]})
    def func(arg="Silicone"):
        ...

    with pytest.raises(ValueError):
        widget = func.Gui()


def test_multiple_gui_with_same_args(qtbot):
    """Test that similarly named arguments are independent of one another."""

    @magicgui
    def example1(a=2):
        return a

    @magicgui
    def example2(a=5):
        return a

    w1 = example1.Gui()
    w2 = example2.Gui()
    # they get their initial values from the function sigs
    assert w1.a == 2
    assert w2.a == 5
    # settings one doesn't affect the other
    w1.a = 10
    assert w1.a == 10
    assert w2.a == 5
    # vice versa...
    w2.a = 4
    assert w1.a == 10
    assert w2.a == 4
    # calling the original equations updates the function defaults
    assert example1() == 10
    assert example2() == 4


def test_multiple_gui_instance_independence(qtbot):
    """Test that multiple instance of the same decorated function are independent."""

    @magicgui
    def example(a=2):
        return a

    w1 = example.Gui()
    w2 = example.Gui()
    # they get their initial values from the function sigs
    assert w1.a == 2
    assert w2.a == 2
    # settings one doesn't affect the other
    w1.a = 10
    assert w1.a == 10
    assert w2.a == 2
    # vice versa...
    w2.a = 4
    assert w1.a == 10
    assert w2.a == 4

    # BEWARE! When setting multiple GUIs like this, calling the original function will
    # return the results from the second widget.
    assert example() == w2() == 4
    # the first function can only be accessed by calling the GUI
    assert w1() == 10


def test_ignore_param(qtbot):
    """Test that the ignore option works."""

    @magicgui(ignore=["b", "c"])
    def func(a: str = "string", b: int = 3, c=7.1) -> str:
        return "works"

    gui = func.Gui()
    assert hasattr(gui, "a")
    assert not hasattr(gui, "b")
    assert not hasattr(gui, "c")
    func()


def test_bad_options(qtbot):
    """Test that the ignore option works."""
    with pytest.raises(TypeError):

        @magicgui(b=7)  # type: ignore
        def func(a="string", b=3, c=7.1):
            return "works"


def test_signature_repr(qtbot):
    """Test that the gui makes a proper signature."""

    @magicgui
    def func(a="string", b=3, c=7.1):
        ...

    gui = func.Gui()
    assert gui._current_signature() == str(signature(func))

    # make sure it is up to date
    gui.b = 0
    assert gui._current_signature() == "(a='string', b=0, c=7.1)"
    assert repr(gui) == "<MagicGui: func(a='string', b=0, c=7.1)>"
