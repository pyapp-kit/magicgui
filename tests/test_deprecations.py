from magicgui import magicgui


def test_events_deprecation():
    @magicgui
    def f(x=1):
        ...

    def _cb(event):
        assert event.value == 2

    f.x.changed.connect(_cb)
    f.x.value = 2
