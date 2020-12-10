"""Simple demonstration of magicgui."""
from magicgui import magicgui


@magicgui(
    auto_call=True,
    result_widget=True,
    input={"widget_type": "LogSlider", "maximum": 10000, "minimum": 1},
)
def slider(input=1):
    return round(input, 4)


slider.show(run=True)
