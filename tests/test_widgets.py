import inspect
from unittest.mock import MagicMock

import pytest
from tests import MyInt

from magicgui import magicgui, use_app, widgets
from magicgui.widgets._bases import ValueWidget


@pytest.mark.parametrize(
    "WidgetClass",
    [
        getattr(widgets, n)
        for n in widgets.__all__
        if n not in ("Widget", "FunctionGui", "MainFunctionGui")
    ],
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

    def _mgui_get_visible(self): ... # noqa
    def _mgui_set_visible(self): ... # noqa
    def _mgui_get_enabled(self): ... # noqa
    def _mgui_set_enabled(self, enabled): ... # noqa
    def _mgui_get_parent(self): ... # noqa
    def _mgui_set_parent(self, widget): ... # noqa
    def _mgui_get_native_widget(self): return MagicMock()  # noqa
    def _mgui_bind_parent_change_callback(self, callback): ... # noqa
    def _mgui_render(self): ... # noqa
    def _mgui_get_width(self): ... # noqa
    def _mgui_set_width(self, value: int): ... # noqa
    def _mgui_get_min_width(self): ... # noqa
    def _mgui_set_min_width(self, value: int): ... # noqa
    def _mgui_get_max_width(self): ... # noqa
    def _mgui_set_max_width(self, value: int): ... # noqa
    def _mgui_get_height(self): ... # noqa
    def _mgui_set_height(self, value: int): ... # noqa
    def _mgui_get_min_height(self): ... # noqa
    def _mgui_set_min_height(self, value: int): ... # noqa
    def _mgui_get_max_height(self): ... # noqa
    def _mgui_set_max_height(self, value: int): ... # noqa
    def _mgui_get_value(self): ... # noqa
    def _mgui_set_value(self, value): ... # noqa
    def _mgui_bind_change_callback(self, callback): ... # noqa
    def _mgui_get_tooltip(self, value): ... # noqa
    # def _mgui_set_tooltip(self, value): ... # noqa


class MyValueWidget(MyBadWidget):
    """Complete protocol implementation... should work."""

    def _mgui_set_tooltip(self, value): ... # noqa
# fmt: on


def test_custom_widget():
    """Test that create_widget works with arbitrary backend implementations."""
    # by implementing the ValueWidgetProtocol, magicgui will know to wrap the above
    # widget with a widgets._bases.ValueWidget
    assert isinstance(
        widgets.create_widget(1, widget_type=MyValueWidget), ValueWidget  # type:ignore
    )


def test_custom_widget_fails():
    """Test that create_widget works with arbitrary backend implementations."""
    with pytest.raises(TypeError) as err:
        widgets.create_widget(1, widget_type=MyBadWidget)  # type: ignore
    assert "does not implement 'WidgetProtocol'" in str(err)
    assert "Missing methods: {'_mgui_set_tooltip'}" in str(err)


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

    assert not widget.visible
    widget.show()
    assert widget.visible

    assert widget.parent is None
    container.append(widget)
    assert widget.parent is container.native
    widget.parent = None
    assert widget.parent is None
    assert widget.label == "my name"
    widget.label = "A different label"
    assert widget.label == "A different label"
    assert widget.width < 100
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
    assert widget.options == {
        "max": 100,
        "min": 0,
        "step": 1,
        "enabled": False,
        "visible": False,
    }


def test_tooltip():
    label = widgets.Label()
    assert not label.tooltip
    label.tooltip = "My Tooltip"
    assert label.tooltip == "My Tooltip"


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

    assert container.layout == "vertical"
    with pytest.raises(NotImplementedError):
        container.layout = "horizontal"

    assert all(x in dir(container) for x in ["labela", "labelb"])

    assert container.margins
    container.margins = (8, 8, 8, 8)
    assert container.margins == (8, 8, 8, 8)

    del container[1:]
    del container[-1]
    assert not container


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


def test_labeled_widget_container():
    """Test that _LabeledWidgets follow their children."""
    from magicgui.widgets._concrete import _LabeledWidget

    w1 = widgets.Label(value="hi", name="w1")
    w2 = widgets.Label(value="hi", name="w2")
    container = widgets.Container(widgets=[w1, w2], layout="vertical")
    assert w1._labeled_widget
    lw = w1._labeled_widget()
    assert isinstance(lw, _LabeledWidget)
    assert not lw.visible
    container.show()
    assert w1.visible
    assert lw.visible
    w1.hide()
    assert not w1.visible
    assert not lw.visible
    w1.label = "another label"
    assert lw._label_widget.value == "another label"


def test_visible_in_container():
    """Test that visibility depends on containers."""
    w1 = widgets.Label(value="hi", name="w1")
    w2 = widgets.Label(value="hi", name="w2")
    w3 = widgets.Label(value="hi", name="w2", visible=False)
    container = widgets.Container(widgets=[w2, w3])
    assert not w1.visible
    assert not w2.visible
    assert not w3.visible
    assert not container.visible
    container.show()
    assert container.visible
    assert w2.visible
    assert not w3.visible
    w1.show()
    assert w1.visible


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


def test_bound_values():
    """Test that we can bind a "permanent" value override to a parameter."""

    @magicgui(x={"bind": 10})
    def f(x: int = 5):
        return x

    # bound values hide the widget by default
    assert not f.x.visible
    assert f() == 10
    f.x.unbind()
    assert f() == 5


def test_binding_None():
    """Test that we can bind a "permanent" value override to a parameter."""

    @magicgui(x={"bind": None})
    def f(x: int = 5):
        return x

    assert f() is None
    f.x.unbind()
    assert f() == 5


def test_bound_values_visible():
    """Test that we force a bound widget to be visible."""

    @magicgui(x={"bind": 10, "visible": True})
    def f(x: int = 5):
        return x

    f.show()
    assert f.x.visible
    assert f() == 10
    f.x.unbind()
    assert f() == 5


def test_bound_callables():
    """Test that we can use a callable as a bound value."""

    @magicgui(x={"bind": lambda x: 10})
    def f(x: int = 5):
        return x

    assert f() == 10
    f.x.unbind()
    assert f() == 5


def test_bound_callable_without_calling():
    """Test that we can use a callable as a bound value, but return it directly."""

    def callback():
        return "hi"

    @magicgui
    def f(x: int = 5):
        return x

    assert f() == 5
    f.x.bind(callback, call=False)
    assert f() == callback
    assert f()() == "hi"


def test_bound_callable_catches_recursion():
    """Test that accessing widget.value raises an informative error message.

    (... rather than a recursion error)
    """

    @magicgui(x={"bind": lambda x: x.value * 2})
    def f(x: int = 5):
        return x

    with pytest.raises(RuntimeError):
        assert f() == 10
    f.x.unbind()
    assert f() == 5

    # use `get_value` within the callback if you need to access widget.value
    f.x.bind(lambda x: x.get_value() * 4)
    assert f() == 20


def test_reset_choice_recursion():
    """Test that reset_choices recursion works for multiple types of widgets."""
    x = 0

    def get_choices(widget):
        nonlocal x
        x += 1
        return list(range(x))

    @magicgui(c={"choices": get_choices})
    def f(c):
        pass

    assert f.c.choices == (0,)

    container = widgets.Container(widgets=[f])
    container.reset_choices()
    assert f.c.choices == (0, 1)
    container.reset_choices()
    assert f.c.choices == (0, 1, 2)


def test_progressbar():
    """Test manually controlling a progressbar."""

    @magicgui(pbar={"min": 20, "max": 40, "step": 2, "value": 30})
    def t(pbar: widgets.ProgressBar):
        assert pbar.get_value() == 32
        pbar.decrement()
        assert pbar.get_value() == 30
        pbar.step = 5
        assert pbar.get_value() == 35
        pbar.decrement(10)
        assert pbar.get_value() == 25


def test_container_indexing_with_native_mucking():
    """Mostly make sure that the inner model isn't messed up.

    keeping indexes with a manipulated native model *may* be something to do in future.
    """
    l1 = widgets.Label(name="l1")
    l2 = widgets.Label(name="l2")
    l3 = widgets.Label(name="l3")
    c = widgets.Container(widgets=[l1, l2, l3])
    assert c[-1] == l3
    # so far they should be in sync
    native = c.native.layout()
    assert native.count() == len(c)
    # much with native layout
    native.addStretch()
    # haven't changed the magicgui container
    assert len(c) == 3
    assert c[-1] == l3
    # though it has changed the native model
    assert native.count() == 4


def test_main_function_gui():
    """Test that main_window makes the widget a top level main window with menus."""

    @magicgui(main_window=True)
    def add(num1: int, num2: int) -> int:
        """Adds the given two numbers, returning the result.

        The function assumes that the two numbers can be added and does
        not perform any prior checks.

        Parameters
        ----------
        num1 , num2 : int
            Numbers to be added

        Returns
        -------
        int
            Resulting integer
        """

    assert not add.visible
    add.show()
    assert add.visible

    assert isinstance(add, widgets.MainFunctionGui)
    add._show_docs()
    assert isinstance(add._help_text_edit, widgets.TextEdit)
    assert add._help_text_edit.value.startswith("Adds the given two numbers")
    assert add._help_text_edit.read_only
