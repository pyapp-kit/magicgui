#!/usr/bin/env python

"""Tests for `magicgui` package."""

from enum import Enum
from inspect import signature

import pytest
from qtpy.QtCore import Qt

from magicgui import magicgui, register_type, type_map, widgets


@pytest.fixture
def magic_func():
    """Test function decorated by magicgui."""

    @magicgui(call_button="my_button", auto_call=True)
    def func(a: str = "works", b: int = 3, c=7.1) -> str:
        return a + str(b)

    return func


def test_magicgui(magic_func):
    """Test basic magicgui functionality."""
    assert magic_func() == "works3"
    assert magic_func.a.value == "works"
    assert magic_func.b.value == 3
    assert magic_func.c.value == 7.1
    assert isinstance(magic_func.a, widgets.LineEdit)
    assert isinstance(magic_func.b, widgets.SpinBox)
    assert isinstance(magic_func.c, widgets.FloatSpinBox)

    magic_func.show()
    assert magic_func.visible

    a = magic_func.a  # save ref
    assert magic_func.index(a) == 0
    # we can delete widgets
    del magic_func.a
    with pytest.raises(AttributeError):
        getattr(magic_func, "a")

    # they disappear from the layout
    with pytest.raises(ValueError):
        magic_func.index(a)


def test_overriding_widget_type(qtbot):
    """Test overriding the widget type of a parameter."""
    # a will now be a LineEdit instead of a spinbox
    @magicgui(a={"widget_type": "LineEdit"})
    def func(a: int = 1):
        pass

    assert isinstance(func.a, widgets.LineEdit)
    assert func.a.value == "1"


def test_no_type_provided(qtbot):
    """Test position args with unknown type."""

    @magicgui
    def func(a):
        pass

    assert isinstance(func.a, widgets.LiteralEvalLineEdit)


def test_call_button(qtbot):
    """Test that the call button has been added, and pressing it calls the function."""

    @magicgui(call_button="my_button", auto_call=True)
    def func(a: int, b: int = 3, c=7.1):
        assert a == 7

    assert hasattr(func, "_call_button")
    assert isinstance(func._call_button, widgets.PushButton)
    func.a.value = 7


def test_auto_call(qtbot, magic_func):
    """Test that changing a parameter calls the function."""
    # changing the widget parameter calls the function
    with qtbot.waitSignal(magic_func.called, timeout=1000):
        magic_func.b.value = 6

    # changing the gui calls the function
    with qtbot.waitSignal(magic_func.called, timeout=1000):
        qtbot.keyClick(magic_func.a.native, Qt.Key_A, Qt.ControlModifier)
        qtbot.keyClick(magic_func.a.native, Qt.Key_Delete)


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

    assert func.arg.value == Medium.Water
    assert isinstance(func.arg, widgets.ComboBox)
    assert list(func.arg.choices) == list(Medium.__members__.values())


def test_dropdown_list_from_choices(qtbot):
    """Test that providing the 'choices' argument with a list of strings works."""
    CHOICES = ["Oil", "Water", "Air"]

    @magicgui(arg={"choices": CHOICES})
    def func(arg="Water"):
        ...

    assert func.arg.value == "Water"
    assert isinstance(func.arg, widgets.ComboBox)
    assert list(func.arg.choices) == CHOICES

    with pytest.raises(ValueError):
        # the default value must be in the list
        @magicgui(arg={"choices": ["Oil", "Water", "Air"]})
        def func(arg="Silicone"):
            ...


def test_dropdown_list_from_callable(qtbot):
    """Test that providing the 'choices' argument with a callable works."""
    CHOICES = ["Oil", "Water", "Air"]

    def get_choices(gui):
        return CHOICES

    @magicgui(arg={"choices": get_choices})
    def func(arg="Water"):
        ...

    assert func.arg.value == "Water"
    assert isinstance(func.arg, widgets.ComboBox)
    assert list(func.arg.choices) == CHOICES

    func.reset_choices()


@pytest.mark.xfail(reason="swapping a widget does not remove the old one", strict=True)
def test_changing_widget_types(magic_func):
    """Test set_widget will either update or change an existing widget."""
    assert magic_func.a.value == "works"
    widget1 = magic_func.a
    assert isinstance(widget1, widgets.LineEdit)

    # changing it to a different type will destroy and create a new widget
    widget2 = widgets.Widget.create(default=1, name="a")
    magic_func.a = widget2
    assert magic_func.a.value == 1
    assert widget1 != widget2
    assert isinstance(widget2, widgets.SpinBox)

    assert magic_func[0] == widget2  # fails


def test_multiple_gui_with_same_args(qtbot):
    """Test that similarly named arguments are independent of one another."""

    @magicgui
    def example1(a=2):
        return a

    @magicgui
    def example2(a=5):
        return a

    # they get their initial values from the function sigs
    assert example1.a.value == 2
    assert example2.a.value == 5
    # settings one doesn't affect the other
    example1.a.value = 10
    assert example1.a.value == 10
    assert example2.a.value == 5
    # vice versa...
    example2.a.value = 4
    assert example1.a.value == 10
    assert example2.a.value == 4
    # calling the original equations updates the function defaults
    assert example1() == 10
    assert example2() == 4


def test_multiple_gui_instance_independence(qtbot):
    """Test that multiple instance of the same decorated function are independent."""

    def example(a=2):
        return a

    w1 = magicgui(example)
    w2 = magicgui(example)
    # they get their initial values from the function sigs
    assert w1.a.value == 2
    assert w2.a.value == 2
    # settings one doesn't affect the other
    w1.a.value = 10
    assert w1.a.value == 10
    assert w2.a.value == 2
    # vice versa...
    w2.a.value = 4
    assert w1.a.value == 10
    assert w2.a.value == 4

    # all instances are independent
    assert example() == 2
    assert w1() == 10
    assert w2() == 4


@pytest.mark.xfail(reason="ignore has not be reimplemented in v0.2.0+", strict=True)
def test_ignore_param(qtbot):
    """Test that the ignore option works."""

    @magicgui(ignore=["b", "c"])
    def func(a: str = "string", b: int = 3, c=7.1) -> str:
        return "works"

    assert hasattr(func, "a")
    assert not hasattr(func, "b")
    assert not hasattr(func, "c")
    func()


def test_invisible_param(qtbot):
    """Test that the visible option works."""

    @magicgui(a={"visible": False})
    def func(a: str = "string", b: int = 3, c=7.1) -> str:
        return "works"

    assert hasattr(func, "a")
    assert not func.a.visible
    assert func.b.visible
    assert func.c.visible
    func()


def test_bad_options(qtbot):
    """Test that invalid parameter options raise TypeError."""
    with pytest.raises(TypeError):

        @magicgui(b=7)
        def func(a="string", b=3, c=7.1):
            return "works"


@pytest.mark.xfail(reason="MagicSignatures are slightly different")
def test_signature_repr(qtbot):
    """Test that the gui makes a proper signature."""

    def func(a="string", b=3, c=7.1):
        ...

    magic_func = magicgui(func)

    # <MagicSignature (a: str = 'string', b: int = 3, c: float = 7.1)> != <Signature (a='string', b=3, c=7.1)>  # noqa
    assert signature(magic_func) == signature(func)

    # make sure it is up to date
    magic_func.b.value = 0
    assert (
        str(signature(magic_func))
        == "(a: str = 'string', b: float = 0, c: float = 7.1)"
    )
    # assert repr(gui) == "<MagicGui: func(a='string', b=0, c=7.1)>"


def test_unrecognized_types(qtbot):
    """Test error handling when an arg with an unrecognized type is encountered."""

    class Something:
        pass

    with pytest.raises(ValueError):
        # don't know how to handle Something type
        @magicgui
        def func(arg: Something, b: int = 1):
            pass

    # # now it should not raise an error... but `arg` should not be in the gui
    # core.SKIP_UNRECOGNIZED_TYPES = True
    # with pytest.warns(UserWarning):
    #     gui = func.Gui()
    # assert not hasattr(gui, "arg")
    # assert hasattr(gui, "b")


def test_set_choices_raises(qtbot):
    """Test failures on setting choices."""

    @magicgui(mood={"choices": ["happy", "sad"]})
    def func(mood: str = "happy"):
        pass

    with pytest.raises(TypeError):
        func.mood.choices = None
    with pytest.raises(TypeError):
        func.mood.choices = 1


def test_get_choices_raises(qtbot):
    """Test failures on getting choices."""

    @magicgui(mood={"choices": [1, 2, 3]})
    def func(mood: int = 1, hi: str = "hello"):
        pass

    with pytest.raises(AttributeError):
        func.hi.choices

    assert func.mood.choices == (1, 2, 3)


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


@pytest.mark.xfail(reason="labels not yet reimplemented")
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

    gui = magicgui(func, labels=labels)
    assert get_layout_items(gui.layout()) == ["a", "b", "c"]
    gui.set_widget("new", 1, position=1)
    assert get_layout_items(gui.layout()) == ["a", "new", "b", "c"]
    gui.set_widget("new2", 1, position=-2)
    assert get_layout_items(gui.layout()) == ["a", "new", "b", "new2", "c"]

    with pytest.raises(TypeError):
        gui.set_widget("hi", 1, position=1.5)


def test_original_function_works(magic_func):
    """Test that the decorated function is still operational."""
    assert magic_func() == "works3"
    assert magic_func("hi") == "hi3"


def test_show(qtbot, magic_func):
    """Test that the show option works."""
    # assert not magic_func.visible
    magic_func.show()
    assert magic_func.visible


def test_register_types(qtbot):
    """Test that we can register custom widget classes for certain types."""
    # must provide a non-None choices or widget_type
    with pytest.raises(ValueError):
        register_type(str, choices=None)

    register_type(int, widget_type="LineEdit")

    # this works, but choices overrides widget_type, and warns the user
    with pytest.warns(UserWarning):
        register_type(str, choices=["works", "cool", "huh"], widget_type="LineEdit")

    class Main:
        pass

    class Sub(Main):
        pass

    class Main2:
        pass

    class Sub2(Main2):
        pass

    register_type(Main, choices=[1, 2, 3])
    register_type(Main2, widget_type="LineEdit")

    @magicgui
    def func(a: str = "works", b: int = 3, c: Sub = None, d: Sub2 = None):
        return a

    assert isinstance(func.a, widgets.ComboBox)
    assert isinstance(func.b, widgets.LineEdit)
    assert isinstance(func.c, widgets.ComboBox)
    assert isinstance(func.d, widgets.LineEdit)

    del type_map._TYPE_DEFS[str]
    del type_map._TYPE_DEFS[int]


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

    func()
    with pytest.raises(AssertionError):
        func(3)

    @magicgui
    def func2(a=1) -> Sub:
        return a

    func2()


@pytest.mark.xfail(reason="need to rethink how to test this")
def test_parent_changed(qtbot, magic_func):
    """Test that setting MagicGui parent emits a signal."""
    with qtbot.waitSignal(magic_func.parent_changed, timeout=1000):
        magic_func.native.setParent(None)
