import contextlib
import sys
from dataclasses import asdict
from typing import TYPE_CHECKING
from unittest.mock import Mock

import psygnal
import pytest

from magicgui.schema._guiclass import (
    button,
    guiclass,
    is_guiclass,
    unbind_gui_from_instance,
)
from magicgui.widgets import Container


def test_guiclass():
    """Test that the guiclass decorator works as expected."""
    mock = Mock()

    @guiclass
    class Foo:
        a: int = 1
        b: str = "bar"

        @button
        def func(self):
            mock(asdict(self))

        if TYPE_CHECKING:
            gui: Container
            events: psygnal.SignalGroup

    foo = Foo()

    assert foo.a == 1
    assert foo.b == "bar"

    assert isinstance(foo.gui, Container)
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


def test_frozen_guiclass():
    """Test that the guiclass decorator works as expected."""

    with pytest.raises(ValueError, match="not support dataclasses with `frozen=True`"):

        @guiclass(frozen=True)
        class Foo:
            a: int = 1
            b: str = "bar"


@pytest.mark.skipif(sys.version_info < (3, 10), reason="slots are python3.10 or higher")
def test_slots_guiclass():
    """Test that the guiclass decorator works as expected."""

    psyg_version = tuple(int(x) for x in psygnal.__version__.split(".")[:3])
    old_psygnal = psyg_version < (0, 6, 1)

    @guiclass(slots=True)
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
