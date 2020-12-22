import pytest

from magicgui import magicgui, widgets


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
