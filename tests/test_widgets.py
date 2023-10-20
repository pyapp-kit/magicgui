import datetime
import inspect
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple
from unittest.mock import MagicMock, patch

import pytest
from typing_extensions import Annotated

from magicgui import magicgui, types, use_app, widgets
from magicgui.widgets import Container, request_values
from magicgui.widgets.bases import DialogWidget, ValueWidget
from tests import MyInt


# it's important that "qt" be last here, so that it's used for
# the rest of the tests
@pytest.fixture(scope="module", params=["ipynb", "qt"])
def backend(request):
    return request.param


# FIXME: this test needs to come before we start swapping backends between qt and ipynb
# in other tests, otherwise it causes a stack overflow in windows...
# I'm not sure why that is, but it likely means that switching apps mid-process is
# not a good idea.  This should be explored further and perhaps prevented... and
# testing might need to be reorganized to avoid this problem.
def test_bound_callable_catches_recursion():
    """Test that accessing widget.value raises an informative error message.

    (... rather than a recursion error)
    """

    # this should NOT raise here. the function should not be called greedily
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


@pytest.mark.parametrize(
    "WidgetClass",
    [
        getattr(widgets, n)
        for n in widgets.__all__
        if n
        not in (
            "Widget",
            "TupleEdit",
            "FunctionGui",
            "MainFunctionGui",
            "show_file_dialog",
            "request_values",
            "create_widget",
        )
    ],
)
def test_widgets(WidgetClass, backend):
    """Test that we can retrieve getters, setters, and signals for most Widgets."""
    app = use_app(backend)
    if not hasattr(app.backend_module, WidgetClass.__name__):
        pytest.skip(f"no {WidgetClass.__name__!r} in backend {backend!r}")
    wdg: widgets.Widget = WidgetClass()
    wdg.close()


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
    wdg = widgets.create_widget(**kwargs)
    assert isinstance(wdg, expect_type)
    wdg.close()


expectations_annotation = (
    (int, widgets.SpinBox),
    (float, widgets.FloatSpinBox),
    (range, widgets.RangeEdit),
    (str, widgets.LineEdit),
    (bool, widgets.CheckBox),
    (slice, widgets.SliceEdit),
    (datetime.date, widgets.DateEdit),
    (datetime.time, widgets.TimeEdit),
    (datetime.datetime, widgets.DateTimeEdit),
)


@pytest.mark.parametrize("annotation, expected_type", expectations_annotation)
def test_create_widget_annotation(annotation, expected_type):
    wdg = widgets.create_widget(annotation=annotation)
    assert isinstance(wdg, expected_type)
    wdg.close()


def test_create_widget_annotation_overwritte_parrams():
    wdg1 = widgets.create_widget(annotation=widgets.ProgressBar)
    assert isinstance(wdg1, widgets.ProgressBar)
    assert wdg1.visible
    wdg2 = widgets.create_widget(
        annotation=Annotated[widgets.ProgressBar, {"visible": False}]
    )
    assert isinstance(wdg2, widgets.ProgressBar)
    assert not wdg2.visible


# fmt: off
class MyBadWidget:
    """INCOMPLETE widget implementation and will error."""
    def _mgui_close_widget(self): ...
    def _mgui_get_visible(self): ...
    def _mgui_set_visible(self): ...
    def _mgui_get_enabled(self): ...
    def _mgui_set_enabled(self, enabled): ...
    def _mgui_get_parent(self): ...
    def _mgui_set_parent(self, widget): ...
    def _mgui_get_native_widget(self): return MagicMock()
    def _mgui_get_root_native_widget(self): ...
    def _mgui_bind_parent_change_callback(self, callback): ...
    def _mgui_render(self): ...
    def _mgui_get_width(self): ...
    def _mgui_set_width(self, value: int): ...
    def _mgui_get_min_width(self): ...
    def _mgui_set_min_width(self, value: int): ...
    def _mgui_get_max_width(self): ...
    def _mgui_set_max_width(self, value: int): ...
    def _mgui_get_height(self): ...
    def _mgui_set_height(self, value: int): ...
    def _mgui_get_min_height(self): ...
    def _mgui_set_min_height(self, value: int): ...
    def _mgui_get_max_height(self): ...
    def _mgui_set_max_height(self, value: int): ...
    def _mgui_get_value(self): ...
    def _mgui_set_value(self, value): ...
    def _mgui_bind_change_callback(self, callback): ...
    def _mgui_get_tooltip(self, value): ...
    # def _mgui_set_tooltip(self, value): ...


class MyValueWidget(MyBadWidget):
    """Complete protocol implementation... should work."""
    def _mgui_set_tooltip(self, value): ...
# fmt: on


def test_custom_widget():
    """Test that create_widget works with arbitrary backend implementations."""
    # by implementing the ValueWidgetProtocol, magicgui will know to wrap the above
    # widget with a widgets._bases.ValueWidget
    with pytest.warns(UserWarning, match="must accept a `parent` Argument"):
        wdg = widgets.create_widget(1, widget_type=MyValueWidget)  # type:ignore
    assert isinstance(wdg, ValueWidget)
    wdg.close()


def test_custom_widget_fails():
    """Test that create_widget works with arbitrary backend implementations."""
    with pytest.raises(TypeError) as err:
        widgets.create_widget(1, widget_type=MyBadWidget)  # type: ignore
    assert "does not implement 'WidgetProtocol'" in str(err)
    assert "Missing methods: {'_mgui_set_tooltip'}" in str(err)


def test_extra_kwargs_error():
    """Test that unrecognized kwargs gives a FutureWarning."""
    with pytest.raises(TypeError) as wrn:
        widgets.Label(unknown_kwarg="hi")
    assert "unexpected keyword argument" in str(wrn)


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
    assert widget.parent is container
    widget.parent = None
    assert widget.parent is None
    assert widget.label == "my name"
    widget.label = "A different label"
    assert widget.label == "A different label"

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
        "max": 999,
        "min": 0,
        "step": None,
        "enabled": False,
        "visible": False,
    }
    widget.close()


def test_width_height():
    widget = widgets.create_widget(value=1, name="my_name")
    widget.show()
    assert widget.visible
    assert widget.width < 100

    widget.width = 150.01
    assert widget.width == 150
    widget.min_width = 100.01
    assert widget.min_width == 100
    widget.max_width = 200.01
    assert widget.max_width == 200

    widget.height = 150.01
    assert widget.height == 150
    widget.min_height = 100.01
    assert widget.min_height == 100
    widget.max_height = 200.01
    assert widget.max_height == 200


def test_tooltip():
    label = widgets.Label()
    assert not label.tooltip
    label.tooltip = "My Tooltip"
    assert label.tooltip == "My Tooltip"


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
    combo.close()


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


def test_bound_unknown_type_annotation():
    """Test that we can bind a "permanent" value override to a parameter."""

    import numpy as np

    def _provide_value(_):
        return np.array(1)

    @magicgui(arr={"bind": _provide_value})
    def f(arr: np.ndarray) -> np.ndarray:
        return arr

    assert f() == np.array(1)


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


def test_bound_not_called():
    """Test that"""
    mock = MagicMock()
    f = magicgui(lambda a: None, a={"bind": mock})
    # the bind function should not be called when creating the widget
    mock.assert_not_called()
    # the bind function should be called when getting the value
    _ = f.a.value
    mock.assert_called_once_with(f.a)


def test_progressbar():
    """Test manually controlling a progressbar."""

    @magicgui(pbar={"min": 20, "max": 40, "step": 2, "value": 30})
    def t(pbar: widgets.ProgressBar):
        assert pbar.get_value() == 30
        pbar.decrement()
        assert pbar.get_value() == 28
        pbar.step = 5
        assert pbar.get_value() == 28
        pbar.increment()
        assert pbar.get_value() == 33
        pbar.decrement(10)
        assert pbar.get_value() == 23
        return pbar.get_value()

    assert t() == 23


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
    add.close()


def test_range_widget():
    args = (-100, 1000, 2)
    rw = widgets.RangeEdit(*args)
    v = rw.value
    assert isinstance(v, range)
    assert (v.start, v.stop, v.step) == args


def test_range_widget_max():
    # max will override and restrict the possible values
    rw = widgets.RangeEdit(-100, 250, 1, max=(0, 500, 1))
    v = rw.value
    assert isinstance(v, range)
    assert (rw.start.max, rw.stop.max, rw.step.max) == (0, 500, 1)

    with pytest.raises(ValueError):
        rw = widgets.RangeEdit(100, 300, 5, max=(0, 500, 5))


def test_range_widget_min():
    # max will override and restrict the possible values
    rw = widgets.RangeEdit(2, 1000, 5, min=(0, 500, 5))
    v = rw.value
    assert isinstance(v, range)
    assert (rw.start.min, rw.stop.min, rw.step.min) == (0, 500, 5)

    with pytest.raises(ValueError):
        rw = widgets.RangeEdit(-100, 1000, 5, min=(0, 500, 5))


def test_range_value_none():
    """Test that arg: int = None defaults to 0"""

    @magicgui
    def f(x: Optional[int] = None):  # type: ignore
        ...

    assert f.x.value == 0
    rw = widgets.SpinBox(value=None)
    assert rw.value == 0


@pytest.mark.parametrize(
    "value,maksimum", [(10, 999), (None, 999), (1000, 9999), (1500, 9999)]
)
def test_range_big_value(value, maksimum):
    rw = widgets.SpinBox(value=value)
    assert rw.value == (value if value is not None else 0)
    rw.max = maksimum


def test_range_negative_value():
    rw = widgets.SpinBox(value=-10)
    assert rw.value == -10
    assert rw.min == -10


def test_adaptive():
    """Turn on and off adaptive step."""

    rw = widgets.SpinBox()
    assert rw.adaptive_step
    assert rw.step is None
    rw.adaptive_step = False
    assert not rw.adaptive_step
    assert rw.step == 1
    rw.step = None
    assert rw.adaptive_step
    assert rw.step is None
    rw.step = 3
    assert not rw.adaptive_step
    assert rw.step == 3

    rw = widgets.SpinBox(step=2)
    assert not rw.adaptive_step
    assert rw.step == 2
    rw.adaptive_step = True
    assert rw.adaptive_step
    assert rw.step is None
    rw.adaptive_step = False
    assert not rw.adaptive_step
    assert rw.step == 2


def test_exception_range_out_of_range():
    with pytest.raises(ValueError):
        widgets.SpinBox(value=10000, max=1000)

    with pytest.raises(ValueError):
        widgets.SpinBox(value=-10, min=0)


def test_file_dialog_events():
    """Test that file dialog events emit the value of the line_edit."""
    fe = widgets.FileEdit(value="hi")
    mock = MagicMock()
    fe.changed.connect(mock)
    fe.line_edit.value = "world"
    mock.assert_called_once_with(Path("world"))


def test_file_dialog_button_events():
    """Test that clicking the file dialog button doesn't emit an event."""
    fe = widgets.FileEdit(value="hi")
    mock = MagicMock()
    fe.changed.connect(mock)
    with patch.object(fe, "_show_file_dialog", return_value=""):
        fe.choose_btn.changed.emit("value")
    mock.assert_not_called()
    assert fe.value == Path("hi")


def test_file_edit_values():
    cwd = Path(".").absolute()

    fe = widgets.FileEdit(mode=types.FileDialogMode.EXISTING_FILE)
    assert isinstance(fe.value, Path)

    fe.value = Path("hi")
    assert fe.value == cwd / "hi"

    fe = widgets.FileEdit(mode=types.FileDialogMode.EXISTING_FILE, nullable=True)
    assert fe.value is None

    fe.value = Path("hi")
    assert fe.value == cwd / "hi"

    fe.value = None
    assert fe.value is None

    fe = widgets.FileEdit(mode=types.FileDialogMode.EXISTING_FILES)
    assert fe.value == ()

    fe.value = Path("hi")
    assert fe.value == (cwd / "hi",)

    fe.value = (Path("hi"), Path("world"))
    assert fe.value == (cwd / "hi", cwd / "world")

    fe.value = ()
    assert fe.value == ()


def test_null_events():
    """Test that nullable widgets emit events when their null value is set"""
    wdg = widgets.ComboBox(choices=["a", "b"], nullable=True)
    mock = MagicMock()
    wdg.changed.connect(mock)
    wdg.value = "b"
    mock.assert_called_once()
    mock.reset_mock()
    wdg.value = None
    mock.assert_called_once()
    mock.reset_mock()

    wdg._nullable = False
    wdg.value = "a"
    mock.assert_called_once()
    mock.reset_mock()
    mock.assert_not_called()
    wdg.value = None
    mock.assert_not_called()


@pytest.mark.parametrize("WdgClass", [widgets.FloatSlider, widgets.FloatSpinBox])
@pytest.mark.parametrize("value", [1, 1e6, 1e12, 1e16, 1e22])
def test_extreme_floats(WdgClass, value):
    wdg = WdgClass(value=value, max=value * 10)
    assert round(wdg.value / value, 4) == 1
    assert round(wdg.max / value, 4) == 10

    mock = MagicMock()
    wdg.changed.connect(mock)
    wdg.value = value * 2
    mock.assert_called_once()
    assert round(mock.call_args[0][0] / value, 4) == 2

    _value = 1 / value
    wdg2 = WdgClass(value=_value, step=_value / 10, max=_value * 100)
    assert round(wdg2.value / _value, 4) == 1.0
    wdg.close()
    wdg2.close()


@pytest.mark.parametrize("Cls", [widgets.ComboBox, widgets.RadioButtons])
def test_categorical_widgets(Cls):
    wdg = Cls(
        value=1,
        choices=[("first option", 1), ("second option", 2), ("third option", 3)],
    )

    mock = MagicMock()
    wdg.changed.connect(mock)
    assert isinstance(wdg, widgets.bases.CategoricalWidget)
    assert wdg.value == 1
    assert wdg.current_choice == "first option"
    mock.assert_not_called()
    wdg.value = 2
    mock.assert_called_once_with(2)
    assert wdg.value == 2
    assert wdg.current_choice == "second option"
    assert wdg.choices == (1, 2, 3)

    wdg.del_choice("third option")
    assert wdg.choices == (1, 2)


@pytest.mark.parametrize(
    "Cls,value", [(widgets.ComboBox, "c3"), (widgets.Select, ["c2", "c3"])]
)
def test_reset_choices_emits_once(Cls, value):
    data = ["c1", "c2", "c3"]
    wdg = Cls(
        value=value,
        choices=lambda w: data,
    )

    mock = MagicMock()
    wdg.changed.connect(mock)
    mock.assert_not_called()
    data = ["d2", "d4"]
    wdg.reset_choices()
    mock.assert_called_once()
    data = ["d2", "d4", "d5"]
    wdg.reset_choices()
    mock.assert_called_once()


@pytest.mark.parametrize(
    "Cls,value1,value2",
    [(widgets.ComboBox, "c4", "c1"), (widgets.Select, ["c3", "c4"], ["c1", "c2"])],
)
def test_set_value_emits_once(Cls, value1, value2):
    wdg = Cls(
        value=value1,
        choices=["c1", "c2", "c3", "c4"],
    )

    mock = MagicMock()
    wdg.changed.connect(mock)
    mock.assert_not_called()
    wdg.value = value2
    mock.assert_called_once()
    wdg.value = value2
    mock.assert_called_once()


@pytest.mark.parametrize(
    "Cls,value", [(widgets.ComboBox, "c3"), (widgets.Select, ["c3", "c4"])]
)
def test_set_choices_emits_once(Cls, value):
    wdg = Cls(
        value=value,
        choices=["c1", "c2", "c3", "c4"],
    )

    mock = MagicMock()
    wdg.changed.connect(mock)
    mock.assert_not_called()
    wdg.choices = ["d2", "d4", "d5"]
    mock.assert_called_once()


class MyEnum(Enum):
    A = "a"
    B = "b"


@pytest.mark.parametrize("Cls", [widgets.ComboBox, widgets.RadioButtons])
def test_categorical_widgets_with_enums(Cls):
    wdg = Cls(value=MyEnum.A, choices=MyEnum)

    mock = MagicMock()
    wdg.changed.connect(mock)
    assert isinstance(wdg, widgets.bases.CategoricalWidget)
    assert wdg.value == MyEnum.A
    assert wdg.current_choice == "A"
    mock.assert_not_called()
    wdg.value = MyEnum.B
    mock.assert_called_once_with(MyEnum.B)
    assert wdg.value == MyEnum.B
    assert wdg.current_choice == "B"
    assert wdg.choices == tuple(MyEnum.__members__.values())
    wdg.close()


@pytest.mark.parametrize("Cls", [widgets.ComboBox, widgets.RadioButtons])
def test_categorical_change_choices(Cls):
    """Make sure we can change choices to more or fewer options."""
    a = tuple(range(10))
    wdg = Cls(choices=a)
    assert wdg.choices == a
    b = tuple(range(5))
    wdg.choices = b
    assert wdg.choices == b
    c = tuple(range(15))
    wdg.choices = c
    assert wdg.choices == c


@pytest.mark.parametrize("Cls", [widgets.ComboBox, widgets.RadioButtons])
def test_categorical_change_choices_callable(Cls):
    first_choices = ("a", "b")

    def get_choices(wdg):
        return ("c", "d")

    wdg = Cls(choices=first_choices)
    assert wdg.choices == first_choices
    assert wdg._default_choices == first_choices

    wdg.choices = get_choices

    assert wdg.choices == ("c", "d")
    assert wdg._default_choices == get_choices


@pytest.mark.skipif(use_app().backend_name != "qt", reason="only on qt")
def test_radiobutton_reset_choices():
    """Test that reset_choices doesn't change the number of buttons."""
    from qtpy.QtWidgets import QRadioButton

    wdg = widgets.RadioButtons(choices=["a", "b", "c"])
    assert len(wdg.native.findChildren(QRadioButton)) == 3
    wdg.reset_choices()
    assert len(wdg.native.findChildren(QRadioButton)) == 3


def test_tracking():
    slider = widgets.Slider(tracking=False)
    assert slider.tracking is False
    slider.tracking = True
    assert slider.tracking


def test_select_set_value():
    sel = widgets.Select(value=[1, 3, 4], choices=list(range(10)))
    assert sel.value == [1, 3, 4]
    sel.value = [1, 4, 8]
    assert sel.value == [1, 4, 8]


def test_slider_readeout():
    """Test that the slider readout spinbox visibility works."""
    # FIXME: ugly direct backend access.
    sld = widgets.Slider()
    sld.show()
    backend_slider = sld.native.children()[1]
    assert "SpinBox" in type(backend_slider).__name__
    assert backend_slider.isVisible()

    sld = widgets.Slider(readout=False)
    sld.show()
    backend_slider = sld.native.children()[1]
    assert not backend_slider.isVisible()

    sld = widgets.Slider(readout=True)
    sld.show()
    assert sld.native.children()[1].isVisible()
    sld.readout = False
    assert not sld.native.children()[1].isVisible()


def test_slice_edit_events():
    """Test that changed events of spin boxes inside a slice edit are
    observable from its parent."""
    start, stop, step = 0, 10, 1
    sl = widgets.SliceEdit(start, stop, step)
    container = widgets.Container(widgets=[sl])
    mock = MagicMock()
    container.changed.connect(mock)
    sl.start.changed.emit(sl.value)
    mock.assert_called()
    assert sl.value == slice(start, stop, step)


def test_pushbutton_click_signal():
    btn = widgets.PushButton(text="click me")
    mock = MagicMock()
    mock2 = MagicMock()
    btn.changed.connect(mock)
    btn.clicked.connect(mock2)
    btn.native.click()
    mock.assert_called_once()
    mock2.assert_called_once()


def test_pushbutton_icon(backend: str):
    use_app(backend)
    btn = widgets.PushButton(icon="mdi:folder")
    btn.set_icon("play", "red")
    btn.set_icon(None)

    if backend == "qt":
        with pytest.warns(UserWarning, match="Could not set iconify icon"):
            btn.set_icon("bad:key")


def test_list_edit():
    """Test ListEdit."""
    from typing import List

    mock = MagicMock()

    list_edit = widgets.ListEdit(value=[1, 2, 3])
    list_edit.changed.connect(mock)
    assert list_edit.value == [1, 2, 3]
    assert list_edit.data == [1, 2, 3]
    assert mock.call_count == 0

    list_edit.btn_plus.changed()
    assert list_edit.value == [1, 2, 3, 3]
    assert list_edit.data == [1, 2, 3, 3]
    assert mock.call_count == 1
    mock.assert_called_with([1, 2, 3, 3])

    list_edit.btn_minus.changed()
    assert list_edit.value == [1, 2, 3]
    assert list_edit.data == [1, 2, 3]
    assert mock.call_count == 2
    mock.assert_called_with([1, 2, 3])

    list_edit.data[0] = 0
    assert list_edit.value == [0, 2, 3]
    assert list_edit.data == [0, 2, 3]
    assert mock.call_count == 3
    mock.assert_called_with([0, 2, 3])

    list_edit[0].value = 10
    assert list_edit.value == [10, 2, 3]
    assert list_edit.data == [10, 2, 3]
    assert mock.call_count == 4
    mock.assert_called_with([10, 2, 3])

    list_edit.data[:2] = [6, 5]  # type: ignore
    assert list_edit.value == [6, 5, 3]
    assert list_edit.data == [6, 5, 3]
    assert mock.call_count == 5
    mock.assert_called_with([6, 5, 3])

    del list_edit.data[0]
    assert list_edit.value == [5, 3]
    assert list_edit.data == [5, 3]
    assert mock.call_count == 6
    mock.assert_called_with([5, 3])

    list_edit.value = [2, 1]
    assert list_edit.value == [2, 1]
    assert list_edit.data == [2, 1]
    # NOTE: changed.blocked() does not restore
    assert mock.call_count == 7
    mock.assert_called_with([2, 1])

    @magicgui
    def f1(x=[2, 4, 6]):  # noqa: B006
        pass

    assert type(f1.x) is widgets.ListEdit
    assert f1.x._args_type is int
    assert f1.x.value == [2, 4, 6]

    @magicgui
    def f2(x: List[int]):
        pass

    assert type(f2.x) is widgets.ListEdit
    assert f2.x.annotation == List[int]
    assert f2.x._args_type is int
    assert f2.x.value == []
    f2.x.btn_plus.changed()
    assert f2.x.value == [0]

    @magicgui(
        x={"options": {"widget_type": "Slider", "min": -10, "max": 10, "step": 5}}
    )
    def f3(x: List[int] = [0]):  # noqa: B006
        pass

    assert type(f3.x) is widgets.ListEdit
    assert type(f3.x[0]) is widgets.Slider
    assert f3.x[0].min == -10
    assert f3.x[0].max == 10
    assert f3.x[0].step == 5

    @magicgui
    def f4(x: List[int] = ()):  # type: ignore
        pass

    assert type(f4.x) is widgets.ListEdit
    assert f4.x.annotation == List[int]
    assert f4.x._args_type is int
    assert f4.x.value == []
    f4.x.btn_plus.changed()
    assert type(f4.x[0]) is widgets.SpinBox
    assert f4.x.value == [0]

    @magicgui
    def f5(x: List[Annotated[int, {"max": 3}]]):
        pass

    assert type(f5.x) is widgets.ListEdit
    assert f5.x.annotation == List[int]
    f5.x.btn_plus.changed()
    assert f5.x[0].max == 3


def test_tuple_edit():
    """Test TupleEdit."""
    from typing import Tuple

    mock = MagicMock()

    tuple_edit = widgets.TupleEdit(value=(1, "a", 2.5))
    tuple_edit.changed.connect(mock)
    assert tuple_edit.value == (1, "a", 2.5)
    assert mock.call_count == 0

    tuple_edit[0].value = 2
    assert tuple_edit.value == (2, "a", 2.5)
    assert mock.call_count == 1
    mock.assert_called_with((2, "a", 2.5))

    tuple_edit.value = (2, "xyz", 1.0)
    assert tuple_edit.value == (2, "xyz", 1.0)
    assert mock.call_count == 2
    mock.assert_called_with((2, "xyz", 1.0))

    with pytest.raises(ValueError):
        tuple_edit.value = (2, "x")

    @magicgui
    def f1(x=(2, 4, 6)):
        pass

    assert type(f1.x) is widgets.TupleEdit
    assert f1.x.value == (2, 4, 6)

    @magicgui
    def f2(x: Tuple[int, str]):
        pass

    assert type(f2.x) is widgets.TupleEdit
    assert f2.x.annotation == Tuple[int, str]
    assert f2.x.value == (0, "")

    @magicgui
    def f3(x: Tuple[Annotated[int, {"max": 3}], str]):
        pass

    assert type(f3.x) is widgets.TupleEdit
    assert f2.x.annotation == Tuple[int, str]
    assert f3.x[0].max == 3


def test_request_values(monkeypatch):
    from unittest.mock import Mock

    container = Container()

    mock = Mock()

    def _exec(self, **k):
        mock()
        assert self.native.parent() is container.native
        return True

    monkeypatch.setattr(DialogWidget, "exec", _exec)
    vals = request_values(
        age={"value": 40},
        name={"annotation": str, "label": "Enter your name:"},
        title="Hi! Who are you?",
        parent=container,
    )
    assert vals == {"age": 40, "name": ""}
    mock.assert_called_once()

    mock.reset_mock()
    vals = request_values(
        values={"age": int, "name": str}, title="Hi! Who are you?", parent=container
    )
    assert vals == {"age": 0, "name": ""}
    mock.assert_called_once()


def test_range_slider():
    @magicgui(auto_call=True, range_value={"widget_type": "RangeSlider", "max": 500})
    def func(range_value: Tuple[int, int] = (20, 380)):
        print(range_value)

    assert isinstance(func.range_value, widgets.RangeSlider)
    assert func.range_value.max == 500
    assert func.range_value.value == (20, 380)


def test_float_range_slider():
    @magicgui(auto_call=True, range_value={"widget_type": "FloatRangeSlider", "max": 1})
    def func(range_value: Tuple[float, float] = (0.2, 0.8)):
        print(range_value)

    assert isinstance(func.range_value, widgets.FloatRangeSlider)
    assert func.range_value.max == 1
    assert func.range_value.value == (0.2, 0.8)


def test_literal():
    from typing import Literal, Set

    from typing_extensions import get_args

    Lit = Literal[None, "a", 1, True, b"bytes"]

    @magicgui
    def f(x: Lit):
        ...

    cbox = f.x
    assert type(cbox) is widgets.ComboBox
    assert cbox.choices == get_args(Lit)

    @magicgui
    def f(x: Set[Lit]):
        ...

    sel = f.x
    assert type(sel) is widgets.Select
    assert sel.choices == get_args(Lit)


def test_float_slider_readout():
    sld = widgets.FloatSlider(value=4, min=0.5, max=10.5)
    assert sld.value == 4
    assert sld._widget._readout_widget.value() == 4
    assert sld._widget._readout_widget.minimum() == 0.5
    assert sld._widget._readout_widget.maximum() == 10.5
