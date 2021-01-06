import inspect
from unittest.mock import MagicMock

import pytest
from tests import MyInt

from magicgui import magicgui, use_app, widgets
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
    assert "does not implement 'WidgetProtocol'" in str(err)
    assert "Missing methods: {'_mgui_show_widget'}" in str(err)


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
    """Basic test coverage for getting/setting attributes."""
    widget = widgets.create_widget(value=1, name="my_name")
    container = widgets.Container(labels=False)
    assert widget.enabled
    widget.enabled = False
    assert not widget.enabled

    assert widget.visible
    widget.visible = False
    assert not widget.visible

    assert widget.parent is None
    container.append(widget)
    assert widget.parent is container.native
    widget.parent = None
    assert widget.parent is None
    assert widget.label == "my name"
    widget.label = "A different label"
    assert widget.label == "A different label"
    assert widget.width > 200
    widget.width = 150
    assert widget.width == 150

    assert widget.param_kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    widget.param_kind = inspect.Parameter.KEYWORD_ONLY
    widget.param_kind = "positional_only"
    assert widget.param_kind == inspect.Parameter.POSITIONAL_ONLY
    with pytest.raises(KeyError):
        widget.param_kind = "not a proper param type"
    with pytest.raises(TypeError):
        widget.param_kind = 1

    assert repr(widget) == "SpinBox(value=1, annotation=None, name='my_name')"
    assert widget.options == {"max": 100, "min": 0, "step": 1, "visible": False}


def test_container_widget():
    """Test basic container functionality."""
    container = widgets.Container(labels=False)
    labela = widgets.Label(value="hi", name="labela")
    labelb = widgets.Label(value="hi", name="labelb")
    container.append(labela)
    container.extend([labelb])
    # different ways to index
    assert container[0] == labela
    assert container["labelb"] == labelb
    assert container[:1] == [labela]
    assert container[-1] == labelb

    with pytest.raises(NotImplementedError):
        container[0] = "something"

    assert container.layout == "horizontal"
    with pytest.raises(NotImplementedError):
        container.layout = "vertical"

    assert all(x in dir(container) for x in ["labela", "labelb"])

    assert container.margins
    container.margins = (8, 8, 8, 8)
    assert container.margins == (8, 8, 8, 8)

    del container[1:]
    del container[-1]
    assert not container

    if use_app().backend_name == "qt":
        assert container.native_layout.__class__.__name__ == "QHBoxLayout"


def test_container_label_widths():
    """Test basic container functionality."""
    container = widgets.Container(layout="vertical")
    labela = widgets.Label(value="hi", name="labela")
    labelb = widgets.Label(value="hi", name="I have a very long label")

    def _label_width():
        measure = use_app().get_obj("get_text_width")
        return max(
            measure(w.label)
            for w in container
            if not isinstance(w, widgets._bases.ButtonWidget)
        )

    container.append(labela)
    before = _label_width()
    container.append(labelb)
    assert _label_width() > before


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


def test_unhashable_choice_data():
    """Test that providing unhashable choice data is ok."""
    combo = widgets.ComboBox()
    assert not combo.choices
    combo.choices = ("a", "b", "c")
    assert combo.choices == ("a", "b", "c")
    combo.choices = (("a", [1, 2, 3]), ("b", [1, 2, 5]))
    assert combo.choices == ([1, 2, 3], [1, 2, 5])
    combo.choices = ("x", "y", "z")
    assert combo.choices == ("x", "y", "z")
