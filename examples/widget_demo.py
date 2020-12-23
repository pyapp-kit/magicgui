"""Widget demonstration of magicgui."""

from datetime import datetime
from enum import Enum
from pathlib import Path

from magicgui import magicgui


class Medium(Enum):
    """Enum for various media and their refractive indices."""

    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(
    call_button="Calculate",
    orientation="vertical",
    result_widget=True,
    slider_float={"widget_type": "FloatSlider"},
    filename={"label": "Pick a file:"},
)
def widget_demo(
    boolean=True,
    integer=1,
    spin_float=3.14159,
    slider_float=4.5,
    string="Text goes here",
    dropdown=Medium.Glass,
    datetime=datetime.now(),
    filename=Path.home(),
):
    """Run some computation."""
    return locals().values()


widget_demo.changed.connect(lambda event: print(widget_demo))
widget_demo.show(run=True)
