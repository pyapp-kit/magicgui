import pytest

from magicgui import widgets


@pytest.mark.parametrize(
    "WidgetClass", [getattr(widgets, n) for n in widgets.__all__ if n != "Widget"]
)
def test_widgets(WidgetClass):
    """Test that we can retrieve getters, setters, and signals for most Widgets."""
    _ = WidgetClass()
