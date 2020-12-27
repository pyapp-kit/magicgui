import pytest
from tests import MyInt

from magicgui import magicgui, widgets
from magicgui.application import use_app


@pytest.mark.parametrize(
    "WidgetClass", [getattr(widgets, n) for n in widgets.__all__ if n != "Widget"]
)
def test_widgets(WidgetClass):
    """Test that we can retrieve getters, setters, and signals for most Widgets."""
    _ = WidgetClass()


def test_autocall_no_runtime_error():
    """Make sure changing a value doesn't cause an autocall infinite loop."""

    @magicgui(auto_call=True, result_widget=True)
    def func(input=1):
        return round(input, 4)

    func.input.value = 2


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


def test_empty_widget():
    """The annotation on a widget should always be a resolved type."""
    use_app("qt")

    @magicgui
    def widget():
        pass

    from qtpy.QtCore import Qt
    from qtpy.QtWidgets import QDockWidget, QMainWindow

    main = QMainWindow()
    dw = QDockWidget(main)
    dw.setWidget(widget.native)
    main.addDockWidget(Qt.RightDockWidgetArea, dw)
    assert widget.native.parent() is dw
