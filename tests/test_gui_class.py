from dataclasses import asdict
from unittest.mock import Mock

from magicgui.schema._guiclass import button, guiclass


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

    foo = Foo()
    assert foo.a == 1
    assert foo.b == "bar"
    assert foo.gui.a.value == 1
    assert foo.gui.b.value == "bar"

    foo.gui.a.value = 3
    assert foo.a == 3

    foo.b = "baz"
    assert foo.gui.b.value == "baz"

    foo.func()
    mock.assert_called_once_with({"a": 3, "b": "baz"})
