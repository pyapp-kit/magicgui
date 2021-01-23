"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!
DEPRECATED!  DON'T USE THIS
!!!!!!!!!!!!!!!!!!!!!!!!!!!

This example is just here for aiding in migration to v0.2.0.
see examples/snells_law.py instead

"""

import math
from enum import Enum

from magicgui import event_loop, magicgui


# dropdown boxes are best made by creating an enum
class Medium(Enum):
    """Enum for various media and their refractive indices."""

    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(call_button="calculate", result_widget=True)
def snells_law(aoi=30.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
    """Calculate the angle of refraction given two media and an AOI."""
    if degrees:
        aoi = math.radians(aoi)
    try:
        n1 = n1.value
        n2 = n2.value
        result = math.asin(n1 * math.sin(aoi) / n2)
        return round(math.degrees(result) if degrees else result, 2)
    except ValueError:  # math domain error
        return "TIR!"


with event_loop():

    # snells_law is *already* a gui in magicgui >= 0.2.0
    gui = snells_law.Gui(show=True)  # Gui() is deprecated

    # this syntax is deprecated, use snells_law.n1.changed.conect...
    gui.n1_changed.connect(print)

    # we can connect a callback function to the __call__ event on the function
    gui.called.connect(lambda e: print("result is", e.value))
