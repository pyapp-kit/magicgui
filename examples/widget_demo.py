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


@magicgui(call_button="Calculate", result_widget=True)
def widget_demo(
    boolean=True,
    integer=1,
    float=3.14159,
    string="Text goes here",
    dropdown=Medium.Glass,
    datetime=datetime.now(),
    filename=Path.home(),
):
    """Run some computation."""
    print("Running some computation...")


widget_demo.widgets.changed.connect(print)
widget_demo.show(run=True)
