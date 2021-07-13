import pytest

from magicgui import magicgui


def test_events_deprecation():
    @magicgui
    def f(x=1):
        ...

    def _cb(event):
        assert event.value == 2

    with pytest.warns(FutureWarning):
        f.x.changed.connect(_cb)
    f.x.value = 2
