"""Widget demonstration of magicgui."""

from enum import Enum
from datetime import datetime
import math
from pathlib import Path

from magicgui import event_loop, magicgui


class Medium(Enum):
    """Enum for various media and their refractive indices."""

    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(call_button="Calculate", result={"disabled": True, "fixedWidth": 100})
def widget_demo(
    boolean=True,
    integer=1,
    float=3.14159,
    string="Text goes here",
    dropdown=Medium.Glass,
    datetime=datetime.now(),
    filename=Path.home()
):
    """Run some computation."""
    print("Running some computation...")
    return "Result!"


with event_loop():
    # the original function still works
    # we can create a gui
    gui = widget_demo.Gui(show=True)
    # we can list for changes to parameters in the gui
    # ... these also trigger for direct parameter access on the gui object
    gui.string_changed.connect(print)
    # we can connect a callback function to the __call__ event on the function
    gui.called.connect(lambda x: gui.set_widget("result", str(x), position=-1))
