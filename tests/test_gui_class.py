import contextlib
import sys
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, ClassVar
from unittest.mock import Mock

import psygnal
import pytest
from psygnal import SignalGroupDescriptor

from magicgui.schema._guiclass import (
    GuiBuilder,
    GuiClass,
    button,
    guiclass,
    is_guiclass,
    unbind_gui_from_instance,
)
from magicgui.widgets import Container, PushButton


def test_guiclass() -> None:
    """Test that the guiclass decorator works as expected."""
    mock = Mock()

    @guiclass
    class Foo:
        a: int = 1
        b: str = "bar"

        @button
        def func(self) -> dict:
            d = asdict(self)
            mock(d)
            return d

        # example recommended for type checking
        if TYPE_CHECKING:
            gui: ClassVar[Container]
            events: ClassVar[psygnal.SignalGroup]

    foo = Foo()

    assert foo.a == 1
    assert foo.b == "bar"

    assert isinstance(foo.gui, Container)
    assert isinstance(foo.gui.func, PushButton)
    assert foo.gui.a.value == 1
    assert foo.gui.b.value == "bar"

    foo.gui.a.value = 3
    assert foo.a == 3

    foo.b = "baz"
    assert foo.gui.b.value == "baz"

    foo.func()
    mock.assert_called_once_with({"a": 3, "b": "baz"})
    assert is_guiclass(Foo)
    assert is_guiclass(foo)


def test_guiclass2() -> None:
    """Test that the guiclass descriptor works as expected."""
    mock = Mock()

    # this is a more direct way to create a guiclass, by using GuiBuilder directly
    # and (optionally) using SignalGroupDescriptor
    @dataclass
    class Foo:
        a: int = 1
        b: str = "bar"

        @button
        def func(self) -> dict:
            d = asdict(self)
            mock(d)
            return d

        # with explicit descriptors for type checking
        gui: ClassVar[GuiBuilder] = GuiBuilder()
        # also optional, since GuiBuilder will do it automatically
        events: ClassVar[SignalGroupDescriptor] = SignalGroupDescriptor()

    foo = Foo()

    assert foo.a == 1
    assert foo.b == "bar"

    assert isinstance(foo.gui, Container)
    assert isinstance(foo.gui.get_widget("func"), PushButton)
    assert foo.gui.a.value == 1
    assert foo.gui.b.value == "bar"

    foo.gui.a.value = 3
    assert foo.a == 3

    foo.b = "baz"
    assert foo.gui.b.value == "baz"

    foo.func()
    mock.assert_called_once_with({"a": 3, "b": "baz"})
    assert is_guiclass(Foo)
    assert is_guiclass(foo)


def test_frozen_guiclass() -> None:
    """Test that the guiclass decorator works as expected."""

    with pytest.raises(ValueError, match="not support dataclasses with `frozen=True`"):

        @guiclass(frozen=True)
        class Foo:
            a: int = 1
            b: str = "bar"


def test_on_existing_dataclass() -> None:
    """Test that the guiclass decorator works on pre-existing dataclasses."""

    @guiclass
    @dataclass
    class Foo:
        a: int = 1
        b: str = "bar"

    foo = Foo()
    assert foo.a == 1
    assert foo.b == "bar"
    assert isinstance(foo.gui, Container)


@pytest.mark.skipif(
    sys.version_info < (3, 11), reason="weakref_slot are python3.11 or higher"
)
def test_slots_guiclass() -> None:
    """Test that the guiclass decorator works as expected."""

    psyg_v = tuple(int(x.split("r")[0]) for x in psygnal.__version__.split(".")[:3])
    old_psygnal = psyg_v < (0, 6, 1)

    # if you don't use weakref_slot, it will still work, but you'll get a warning
    # during signal connection on gui-creation
    @guiclass(slots=True, weakref_slot=True)
    class Foo:
        a: int = 1
        b: str = "bar"

    foo = Foo()

    with (
        pytest.warns(UserWarning, match="Please update psygnal")
        if old_psygnal
        else contextlib.nullcontext()
    ):
        gui = foo.gui
        # note that with slots=True, the gui is recreated on every access
        assert foo.gui is not gui

    assert isinstance(gui, Container)
    assert gui.a.value == 1
    foo.b = "baz"
    assert gui.b.value == "baz"
    gui.a.value = 3

    if old_psygnal:
        # no change :(
        assert foo.a == 1
        assert len(gui.a.changed._slots) == 2
    else:
        assert foo.a == 3
        assert len(gui.a.changed._slots) == 3

    unbind_gui_from_instance(gui, foo)
    assert len(gui.a.changed._slots) == 2
    del foo


def test_guiclass_as_class() -> None:
    # variant on @guiclass, using class instead of decorator
    class T2(GuiClass):
        x: int
        y: str = "hi"

        @button
        def foo(self) -> dict:
            return asdict(self)

    t2 = T2(1)
    assert t2.x == 1
    assert t2.y == "hi"
    assert t2.gui.x.value == 1
    assert t2.gui.y.value == "hi"
    t2.gui.x.value = 3
    assert t2.x == 3
    t2.y = "baz"
    assert t2.gui.y.value == "baz"
    assert isinstance(t2.gui.foo, PushButton)
    assert t2.foo() == {"x": 3, "y": "baz"}


def test_path_update() -> None:
    """One off test for FileEdits... which weren't updating.

    (The deeper issue is that things like FileEdit don't subclass ValueWidget...)
    """

    from pathlib import Path

    @guiclass
    class MyGuiClass:
        a: Path = Path("blabla")

    obj = MyGuiClass()
    assert obj.gui.a.value.stem == "blabla"
    assert obj.a.stem == "blabla"

    obj.gui.a.value = "foo"
    assert obj.gui.a.value.stem == "foo"
    assert obj.a.stem == "foo"


def test_name_collisions() -> None:
    """Test that dataclasses can have names colliding with widget attributes."""

    @guiclass
    class Foo:
        name: str = "foo"
        annotation: str = "bar"

    foo = Foo()
    assert isinstance(foo.gui, Container)
    foo.gui.update({"name": "baz", "annotation": "qux"})
    assert asdict(foo) == {"name": "baz", "annotation": "qux"}
