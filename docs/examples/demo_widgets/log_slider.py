"""Simple demonstration of magicgui."""
from magicgui import magicgui


@magicgui(
    auto_call=True,
    result_widget=True,
    input={"widget_type": "LogSlider", "max": 10000, "min": 1, "tracking": False},
)
def slider(input=1):
    return round(input, 4)


slider.show(run=True)
