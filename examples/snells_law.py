"""Simple demonstration of magicgui."""

from enum import Enum
import math

from magicgui import event_loop, magicgui


# dropdown boxes are best made by creating an enum
class Medium(Enum):
    """Enum for various media and their refractive indices."""

    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(call_button="calculate", result={"disabled": True, "fixedWidth": 100})
def snells_law(
    aoi=30.0, n1=Medium.Glass, n2=Medium.Water, degrees=True,
):
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
    # the original function still works
    # we can create a gui
    gui = snells_law.Gui(show=True)
    # we can list for changes to parameters in the gui
    # ... these also trigger for direct parameter access on the gui object
    gui.n1_changed.connect(print)
    # we can connect a callback function to the __call__ event on the function
    gui.called.connect(lambda x: gui.set_widget("result", str(x), position=-1))
