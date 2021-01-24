#!/usr/bin/env python

"""Tests for `magicgui` package."""

import inspect
from enum import Enum

import pytest
from qtpy.QtCore import Qt

from magicgui import magicgui, register_type, type_map, widgets
from magicgui.signature import MagicSignature


@pytest.fixture
def magic_func():
    """Test function decorated by magicgui."""

    @magicgui(call_button="my_button", auto_call=True, labels=False)
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


def test_overriding_widget_type():
    """Test overriding the widget type of a parameter."""
    # a will now be a LineEdit instead of a spinbox
    @magicgui(a={"widget_type": "LineEdit"})
    def func(a: int = 1):
        pass

    assert isinstance(func.a, widgets.LineEdit)
    assert func.a.value == "1"


def test_unrecognized_types():
    """Test that arg with an unrecognized type is hidden."""

    class Something:
        pass

    # don't know how to handle Something type
    @magicgui
    def func(arg: Something, b: int = 1):
        pass

    assert isinstance(func.arg, widgets.EmptyWidget)

    with pytest.raises(TypeError) as e:
        func()
    assert "missing a required argument" in str(e)


def test_no_type_provided():
    """Test position args with unknown type."""

    @magicgui
    def func(a):
        pass

    assert isinstance(func.a, widgets.EmptyWidget)
    with pytest.raises(TypeError) as e:
        func()
    assert "missing a required argument" in str(e)
    assert "@magicgui(a={'bind': value})" in str(e)


def test_bind_out_of_order():
    """Test that binding a value before a non-default argument still gives message."""

    @magicgui(a={"bind": 10})
    def func(a, x):
        pass

    assert isinstance(func.a, widgets.EmptyWidget)
    with pytest.raises(TypeError) as e:
        func()
    assert "missing a required argument" in str(e)
    assert "@magicgui(x={'bind': value})" in str(e)


def test_call_button():
    """Test that the call button has been added, and pressing it calls the function."""

    @magicgui(call_button="my_button", auto_call=True)
    def func(a: int, b: int = 3, c=7.1):
        assert a == 7

    assert hasattr(func, "_call_button")
    assert isinstance(func._call_button, widgets.PushButton)
    func.a.value = 7


def test_auto_call(qtbot, magic_func):
    """Test that changing a parameter calls the function."""

    # TODO: remove qtbot requirement so we can test other backends eventually.

    # changing the widget parameter calls the function
    with qtbot.waitSignal(magic_func.called, timeout=1000):
        magic_func.b.value = 6

    # changing the gui calls the function
    with qtbot.waitSignal(magic_func.called, timeout=1000):
        qtbot.keyClick(magic_func.a.native, Qt.Key_A, Qt.ControlModifier)
        qtbot.keyClick(magic_func.a.native, Qt.Key_Delete)


def test_dropdown_list_from_enum():
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


def test_dropdown_list_from_choices():
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


def test_dropdown_list_from_callable():
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


def test_changing_widget_attr_fails(magic_func):
    """Test set_widget will either update or change an existing widget."""
    assert magic_func.a.value == "works"
    widget1 = magic_func.a
    assert isinstance(widget1, widgets.LineEdit)

    # changing it to a different type will destroy and create a new widget
    widget2 = widgets.create_widget(value=1, name="a")
    with pytest.raises(AttributeError):
        magic_func.a = widget2

    assert magic_func.a == widget1


def test_multiple_gui_with_same_args():
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


def test_multiple_gui_instance_independence():
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


def test_invisible_param():
    """Test that the visible option works."""

    @magicgui(a={"visible": False})
    def func(a: str = "string", b: int = 3, c=7.1) -> str:
        return "works"

    assert hasattr(func, "a")
    func.show()
    assert not func.a.visible
    assert func.b.visible
    assert func.c.visible
    func()


def test_bad_options():
    """Test that invalid parameter options raise TypeError."""
    with pytest.raises(TypeError):

        @magicgui(b=7)  # type: ignore
        def func(a="string", b=3, c=7.1):
            return "works"


# @pytest.mark.xfail(reason="MagicSignatures are slightly different")
def test_signature_repr():
    """Test that the gui makes a proper signature."""

    def func(a: str = "string", b: int = 3, c: float = 7.1):
        return locals()

    magic_func = magicgui(func)

    # the STRING signature representation should be the same as the original function
    assert str(inspect.signature(magic_func)) == str(inspect.signature(func))
    # however, the magic_func signature is an enhance MagicSignature object:
    assert isinstance(inspect.signature(magic_func), MagicSignature)
    assert isinstance(inspect.signature(func), inspect.Signature)

    # make sure it is up to date
    magic_func.b.value = 0
    assert (
        str(inspect.signature(magic_func))
        == "(a: str = 'string', b: int = 0, c: float = 7.1)"
    )


def test_set_choices_raises():
    """Test failures on setting choices."""

    @magicgui(mood={"choices": ["happy", "sad"]})
    def func(mood: str = "happy"):
        pass

    with pytest.raises(TypeError):
        func.mood.choices = None
    with pytest.raises(TypeError):
        func.mood.choices = 1


def test_get_choices_raises():
    """Test failures on getting choices."""

    @magicgui(mood={"choices": [1, 2, 3]})
    def func(mood: int = 1, hi: str = "hello"):
        pass

    with pytest.raises(AttributeError):
        func.hi.choices

    assert func.mood.choices == (1, 2, 3)


@pytest.mark.parametrize(
    "labels",
    [
        pytest.param(
            True, marks=pytest.mark.xfail(reason="indexing still wrong with labels")
        ),
        False,
    ],
    ids=["with-labels", "no-labels"],
)
def test_add_at_position(labels):
    """Test that adding widghet with position option puts widget in the right place."""

    def func(a=1, b=2, c=3):
        pass

    def get_layout_items(gui):
        lay = gui.native.layout()
        items = [lay.itemAt(i).widget()._magic_widget.name for i in range(lay.count())]
        if labels:
            items = list(filter(None, items))
        return items

    gui = magicgui(func, labels=labels)
    assert get_layout_items(gui) == ["a", "b", "c"]
    gui.insert(1, widgets.create_widget(name="new"))
    assert get_layout_items(gui) == ["a", "new", "b", "c"]


def test_original_function_works(magic_func):
    """Test that the decorated function is still operational."""
    assert magic_func() == "works3"
    assert magic_func("hi") == "hi3"


def test_show(magic_func):
    """Test that the show option works."""
    # assert not magic_func.visible
    magic_func.show()
    assert magic_func.visible


def test_register_types():
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


def test_register_return_callback():
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


# @pytest.mark.skip(reason="need to rethink how to test this")
# def test_parent_changed(qtbot, magic_func):
#     """Test that setting MagicGui parent emits a signal."""
#     with qtbot.waitSignal(magic_func.parent_changed, timeout=1000):
#         magic_func.native.setParent(None)


def test_function_binding():
    class MyObject:
        def __init__(self, name):
            self.name = name
            self.counter = 0.0

        @magicgui(auto_call=True)
        def method(self, sigma: float = 1):
            self.counter = self.counter + sigma
            return self.name, self.counter

    a = MyObject("a")
    b = MyObject("b")

    assert a.method() == ("a", 1)
    assert b.method(sigma=4) == ("b", 4)
    assert a.method() == ("a", 2)
    assert b.method() == ("b", 5)


def test_call_count():
    """Test that a function gui remembers how many times it's been called."""

    @magicgui
    def func():
        pass

    assert func.call_count == 0
    func()
    func()
    assert func.call_count == 2
    func.reset_call_count()
    assert func.call_count == 0


def test_tooltips_from_numpydoc():
    """Test that numpydocs docstrings can be used for tooltips."""

    x_tooltip = "override tooltip"
    y_docstring = """A greeting, by default 'hi'. Notice how we miraculously pull
the entirety of the docstring just like that"""

    @magicgui(x={"tooltip": x_tooltip}, z={"tooltip": None})
    def func(x: int, y: str = "hi", z=None):
        """Do a little thing.

        Parameters
        ----------
        x : int
            An integer for you to use
        y : str, optional
            A greeting, by default 'hi'. Notice how we miraculously pull
            the entirety of the docstring just like that
        z : Any, optional
            No tooltip for me please.
        """
        pass

    assert func.x.tooltip == x_tooltip
    assert func.y.tooltip == y_docstring
    assert not func.z.tooltip


def test_duplicated_and_missing_params_from_numpydoc():
    """Test that numpydocs docstrings can be used for tooltips."""

    @magicgui
    def func(x, y, z=None):
        """Do a little thing.

        Parameters
        ----------
        x, y : int
            Integers for you to use
        """
        pass

    assert func.x.tooltip == "Integers for you to use"
    assert func.y.tooltip == "Integers for you to use"
    assert not func.z.tooltip


def test_tooltips_from_google_doc():
    """Test that google docstrings can be used for tooltips."""

    x_docstring = "An integer for you to use"
    y_docstring = """A greeting. Notice how we miraculously pull
the entirety of the docstring just like that"""

    @magicgui
    def func(x: int, y: str = "hi"):
        """Do a little thing.

        Args:
            x (int): An integer for you to use
            y (str, optional): A greeting. Notice how we miraculously pull
                               the entirety of the docstring just like that
        """
        pass

    assert func.x.tooltip == x_docstring
    assert func.y.tooltip == y_docstring


def test_tooltips_from_rest_doc():
    """Test that google docstrings can be used for tooltips."""

    x_docstring = "An integer for you to use"
    y_docstring = """A greeting, by default 'hi'. Notice how we miraculously pull
the entirety of the docstring just like that"""

    @magicgui
    def func(x: int, y: str = "hi", z=None):
        """Do a little thing.

        :param x: An integer for you to use
        :param y: A greeting, by default 'hi'. Notice how we miraculously pull
                  the entirety of the docstring just like that
        :type x: int
        :type y: str
        """
        pass

    assert func.x.tooltip == x_docstring
    assert func.y.tooltip == y_docstring


def test_no_tooltips_from_numpydoc():
    """Test that ``tooltips=False`` hides all tooltips."""

    @magicgui(tooltips=False)
    def func(x: int, y: str = "hi"):
        """Do a little thing.

        Parameters
        ----------
        x : int
            An integer for you to use
        y : str, optional
            A greeting, by default 'hi'
        """
        pass

    assert not func.x.tooltip
    assert not func.y.tooltip


def test_only_some_tooltips_from_numpydoc():
    """Test that we can still show some tooltips with ``tooltips=False``."""
    # tooltips=False, means docstrings wont be parsed at all, but tooltips
    # can still be manually provided.
    @magicgui(tooltips=False, y={"tooltip": "Still want a tooltip"})
    def func(x: int, y: str = "hi"):
        """Do a little thing.

        Parameters
        ----------
        x : int
            An integer for you to use
        y : str, optional
            A greeting, by default 'hi'
        """
        pass

    assert not func.x.tooltip
    assert func.y.tooltip == "Still want a tooltip"


def test_magicgui_type_error():

    with pytest.raises(TypeError):
        magicgui("not a function")  # type: ignore


@magicgui
def self_referencing_function(x: int = 1):
    """Function that refers to itself, and wants the FunctionGui instance."""
    return self_referencing_function


def test_magicgui_self_reference():
    """Test that self-referential magicguis work in global scopes."""

    assert isinstance(self_referencing_function(), widgets.FunctionGui)


def test_local_magicgui_self_reference():
    """Test that self-referential magicguis work in local scopes."""

    @magicgui
    def local_self_referencing_function(x: int = 1):
        """Function that refers to itself, and wants the FunctionGui instance."""
        return local_self_referencing_function

    assert isinstance(local_self_referencing_function(), widgets.FunctionGui)
