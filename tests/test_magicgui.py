#!/usr/bin/env python

"""Tests for `magicgui` package."""

from enum import Enum

import pytest
from inspect import signature
from qtpy import QtWidgets as QtW
from qtpy.QtCore import Qt

from magicgui import magicgui, register_type
from magicgui import core
from magicgui._qt import type2widget


@pytest.fixture
def magic_func():
    """Test function decorated by magicgui."""

    @magicgui(call_button="my_button", auto_call=True)
    def func(a: str = "works", b: int = 3, c=7.1) -> str:
        return a

    return func


@pytest.fixture
def magic_widget(qtbot, magic_func):
    """Test instantiated widget."""
    return magic_func.Gui()


def test_magicgui(magic_widget):
    """Test basic magicgui functionality."""
    assert magic_widget.func() == "works"
    assert magic_widget.a == "works"
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


def test_overriding_widget_type(qtbot):
    """Test overriding the widget type of a parameter."""
    # a will now be a LineEdit instead of a spinbox
    @magicgui(a={"widget_type": QtW.QLineEdit})
    def func(a: int = 1):
        pass

    gui = func.Gui()
    assert isinstance(gui.get_widget("a"), QtW.QLineEdit)
    assert gui.a == "1"


def test_overriding_arg_type(qtbot):
    """Test overriding the widget type of a parameter."""
    # a will now be a LineEdit instead of a spinbox
    @magicgui(a={"dtype": str})
    def func(a=1):
        pass

    gui = func.Gui()
    assert isinstance(gui.get_widget("a"), QtW.QLineEdit)
    assert gui.a == "1"

    # however, type annotations take precedence
    @magicgui(a={"dtype": str})
    def func(a: int = 1):
        pass

    gui = func.Gui()
    assert isinstance(gui.get_widget("a"), QtW.QSpinBox)
    assert gui.a == 1


def test_no_type_provided(qtbot):
    """Test position args with unknown type."""

    @magicgui
    def func(a):
        pass

    gui = func.Gui()
    none_widget = type2widget(type(None))
    assert none_widget
    assert isinstance(gui.get_widget("a"), none_widget)


def test_call_button(qtbot):
    """Test that the call button has been added, and pressing it calls the function."""

    @magicgui(call_button="my_button", auto_call=True)
    def func(a: int, b: int = 3, c=7.1) -> None:
        assert a == 7

    magic_widget = func.Gui()

    assert hasattr(magic_widget, "call_button")
    assert isinstance(magic_widget.call_button, QtW.QPushButton)
    magic_widget.a = 7

    qtbot.mouseClick(magic_widget.call_button, Qt.LeftButton)


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


def test_dropdown_list_from_choices(qtbot):
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


def test_dropdown_list_from_callable(qtbot):
    """Test that providing the 'choices' argument with a callable works."""
    CHOICES = ["Oil", "Water", "Air"]

    def get_choices(gui, arg_type):
        return CHOICES

    @magicgui(arg={"choices": get_choices})
    def func(arg="Water"):
        ...

    widget = func.Gui()
    assert widget.arg == "Water"
    assert isinstance(widget.arg_widget, QtW.QComboBox)
    assert widget.get_choices("arg") == CHOICES
    items = [widget.arg_widget.itemText(i) for i in range(widget.arg_widget.count())]
    assert items == CHOICES

    widget.refresh_choices()
    with pytest.raises(ValueError):
        widget.refresh_choices("nonarg")


def test_changing_widget_types(magic_widget):
    """Test set_widget will either update or change an existing widget."""
    assert magic_widget.a == "works"
    widget1 = magic_widget.get_widget("a")
    assert isinstance(widget1, QtW.QLineEdit)

    # changing it to a different type will destroy and create a new widget
    magic_widget.set_widget("a", 1)
    widget2 = magic_widget.get_widget("a")
    assert magic_widget.a == 1
    assert widget1 != widget2
    assert isinstance(widget2, QtW.QSpinBox)

    # changing it to a different value of the same type will just update the widget.
    magic_widget.set_widget("a", 7)
    widget3 = magic_widget.get_widget("a")
    assert magic_widget.a == 7
    assert widget2 == widget3


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


def test_unrecognized_types(qtbot):
    """Test error handling when an arg with an unrecognized type is encountered."""

    class Something:
        pass

    @magicgui
    def func(arg: Something, b: int = 1):
        pass

    # don't know how to handle Something type
    with pytest.raises(TypeError):
        gui = func.Gui()

    # now it should not raise an error... but `arg` should not be in the gui
    core.SKIP_UNRECOGNIZED_TYPES = True
    gui = func.Gui()
    assert not hasattr(gui, "arg")
    assert hasattr(gui, "b")


def test_set_choices_raises(qtbot):
    """Test failures on setting choices."""

    @magicgui
    def func(mood: str = "happy"):
        pass

    gui = func.Gui()
    with pytest.raises(ValueError):
        gui.set_choices("mood", None)
    with pytest.raises(TypeError):
        gui.set_choices("mood", 1)


def test_get_choices_raises(qtbot):
    """Test failures on getting choices."""

    @magicgui(mood={"choices": [1, 2, 3]})
    def func(mood: int = 1, hi: str = "hello"):
        pass

    gui = func.Gui()
    with pytest.raises(KeyError):
        gui.get_choices("hi")


@pytest.mark.skip(reason="does not yet work")
def test_positions(qtbot):
    """Test that providing position options puts widget in the right place."""

    def func(a=1, b=2, c=3):
        pass

    def get_layout_items(layout):
        return [layout.itemAt(i).widget().objectName() for i in range(layout.count())]

    gui = magicgui(func).Gui()
    assert get_layout_items(gui.layout()) == ["a", "b", "c"]
    gui = magicgui(func, a={"position": 2}, b={"position": 1}).Gui()
    assert get_layout_items(gui.layout()) == ["c", "b", "a"]


@pytest.mark.parametrize("labels", [True, False], ids=["with-labels", "no-labels"])
def test_add_at_position(labels, qtbot):
    """Test that adding widghet with position option puts widget in the right place."""

    def func(a=1, b=2, c=3):
        pass

    def get_layout_items(layout):
        items = [layout.itemAt(i).widget().objectName() for i in range(layout.count())]
        if labels:
            items = list(filter(None, items))
        return items

    gui = magicgui(func, labels=labels).Gui()
    assert get_layout_items(gui.layout()) == ["a", "b", "c"]
    gui.set_widget("new", 1, position=1)
    assert get_layout_items(gui.layout()) == ["a", "new", "b", "c"]
    gui.set_widget("new2", 1, position=-2)
    assert get_layout_items(gui.layout()) == ["a", "new", "b", "new2", "c"]

    with pytest.raises(TypeError):
        gui.set_widget("hi", 1, position=1.5)


def test_original_function_works(magic_func):
    """Test that the decorated function is still operational."""
    assert magic_func() == "works"
    assert magic_func("hi") == "hi"


def test_show(qtbot, magic_func):
    """Test that the show option works."""
    gui = magic_func.Gui(show=True)
    assert gui.isVisible()


def test_register_types(qtbot):
    """Test that we can register custom widget classes for certain types."""
    # must provide a non-None choices or widget_type
    with pytest.raises(ValueError):
        register_type(str, choices=None)

    register_type(int, widget_type=QtW.QLineEdit)

    # this works, but choices overrides widget_type, and warns the user
    with pytest.warns(UserWarning):
        register_type(str, choices=["works", "cool", "huh"], widget_type=QtW.QLineEdit)

    class Main:
        pass

    class Sub(Main):
        pass

    class Main2:
        pass

    class Sub2(Main2):
        pass

    register_type(Main, choices=[1, 2, 3])
    register_type(Main2, widget_type=QtW.QLineEdit)

    @magicgui
    def func(a: str = "works", b: int = 3, c: Sub = None, d: Sub2 = None):
        return a

    gui = func.Gui()
    assert isinstance(gui.get_widget("a"), QtW.QComboBox)
    assert isinstance(gui.get_widget("b"), QtW.QLineEdit)
    assert isinstance(gui.get_widget("c"), QtW.QComboBox)
    assert isinstance(gui.get_widget("d"), QtW.QLineEdit)

    core.reset_type(str)
    core.reset_type(int)


def test_register_return_callback(qtbot):
    """Test that registering a return callback works."""

    def check_value(gui, value, rettype):
        assert value == 1

    class Base:
        pass

    class Sub(Base):
        pass

    register_type(int, return_callback=check_value)
    register_type(Base, return_callback=check_value)

    @magicgui
    def func(a=1) -> int:
        return a

    _ = func.Gui()
    func()
    with pytest.raises(AssertionError):
        func(3)

    @magicgui
    def func2(a=1) -> Sub:
        return a

    _ = func2.Gui()
    func2()


def test_parent_changed(qtbot, magic_widget):
    """Test that setting MagicGui parent emits a signal."""
    with qtbot.waitSignal(magic_widget.parentChanged, timeout=1000):
        magic_widget.setParent(None)


def test_layout_raises(qtbot):
    """Test that unrecognized layouts raise an error."""

    @magicgui(layout="df")
    def test(a=1):
        pass

    with pytest.raises(KeyError):
        test.Gui()
