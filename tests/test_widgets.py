from unittest.mock import MagicMock

import pytest
from tests import MyInt

from magicgui import magicgui, widgets
from magicgui.widgets._bases import ValueWidget


@pytest.mark.parametrize(
    "WidgetClass", [getattr(widgets, n) for n in widgets.__all__ if n != "Widget"]
)
def test_widgets(WidgetClass):
    """Test that we can retrieve getters, setters, and signals for most Widgets."""
    _ = WidgetClass()


expectations = (
    [{"value": 1}, widgets.SpinBox],
    [{"value": 1.0}, widgets.FloatSpinBox],
    [{"value": "hi"}, widgets.LineEdit],
    [{"value": "a", "options": {"choices": ["a", "b"]}}, widgets.Combobox],
    [{"value": 1, "widget_type": "Slider"}, widgets.Slider],
)


@pytest.mark.parametrize("kwargs, expect_type", expectations)
def test_create_widget(kwargs, expect_type):
    """Test that various values get turned into widgets."""
    assert isinstance(widgets.create_widget(**kwargs), expect_type)


# fmt: off
class MyBadWidget:
    """INCOMPLETE widget implementation and will error."""

    def _mgui_hide_widget(self): ... # noqa
    def _mgui_get_enabled(self): ... # noqa
    def _mgui_set_enabled(self, enabled): ... # noqa
    def _mgui_get_parent(self): ... # noqa
    def _mgui_set_parent(self, widget): ... # noqa
    def _mgui_get_native_widget(self): return MagicMock()  # noqa
    def _mgui_bind_parent_change_callback(self, callback): ... # noqa
    def _mgui_render(self): ... # noqa
    def _mgui_get_width(self): ... # noqa
    def _mgui_set_min_width(self, value: int): ... # noqa
    def _mgui_get_value(self): ... # noqa
    def _mgui_set_value(self, value): ... # noqa
    def _mgui_bind_change_callback(self, callback): ... # noqa


class MyValueWidget(MyBadWidget):
    """Complete protocol implementation... should work."""

    def _mgui_show_widget(self): ... # noqa
# fmt: on


def test_custom_widget():
    """Test that create_widget works with arbitrary backend implementations."""
    # by implementing the ValueWidgetProtocol, magicgui will know to wrap the above
    # widget with a widgets._bases.ValueWidget
    assert isinstance(widgets.create_widget(1, widget_type=MyValueWidget), ValueWidget)


def test_custom_widget_fails():
    """Test that create_widget works with arbitrary backend implementations."""
    with pytest.raises(TypeError) as err:
        widgets.create_widget(1, widget_type=MyBadWidget)  # type: ignore
    assert "does not implement any known widget protocols" in str(err)


def test_extra_kwargs_warn():
    """Test that unrecognized kwargs gives a FutureWarning."""
    with pytest.warns(FutureWarning) as wrn:
        widgets.Label(unknown_kwarg="hi")
    assert "unexpected keyword arguments" in str(wrn[0].message)


def test_autocall_no_runtime_error():
    """Make sure changing a value doesn't cause an autocall infinite loop."""

    @magicgui(auto_call=True, result_widget=True)
    def func(input=1):
        return round(input, 4)

    func.input.value = 2


def test_basic_widget_attributes():
    """Increase coverage of getting/setting attributes."""
    widget = widgets.create_widget(value=1)
    container = widgets.Container(labels=False)
    events: list = []
    widget.parent_changed.connect(events.append)
    assert widget.enabled
    assert widget.parent is None
    assert len(events) == 0
    container.append(widget)  # should change the parent
    assert len(events)
    assert widget.parent is container.native


def test_delete_widget():
    """We can delete widgets from containers."""
    a = widgets.Label(name="a")
    container = widgets.Container(widgets=[a])
    # we can delete widgets
    del container.a
    with pytest.raises(AttributeError):
        getattr(container, "a")

    # they disappear from the layout
    with pytest.raises(ValueError):
        container.index(a)


def test_widget_resolves_forward_ref():
    """The annotation on a widget should always be a resolved type."""

    @magicgui
    def widget(x: "tests.MyInt"):  # type: ignore  # noqa
        pass

    assert widget.x.annotation is MyInt
