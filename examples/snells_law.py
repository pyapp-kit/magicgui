from enum import Enum
import math

from magicgui import event_loop, magicgui


# dropdown boxes are best made by creating an enum
class Medium(Enum):
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(call_button="calculate")
def snells_law(
    angle_of_incidence=30.0,
    medium_1=Medium.Glass,
    medium_2=Medium.Water,
    degrees=True,
    angle_of_refraction="...",
):
    if degrees:
        angle_of_incidence = math.radians(angle_of_incidence)
    try:
        n1 = medium_1.value
        n2 = medium_2.value
        result = math.asin(n1 * math.sin(angle_of_incidence) / n2)
        return round(math.degrees(result) if degrees else result, 2)
    except ValueError:  # math domain error
        return "TIR!"


with event_loop():
    # the original function still works
    print(snells_law())
    # we can create a gui
    gui = snells_law.Gui(show=True)
    # we can list for changes to parameters in the gui
    # ... these also trigger for direct parameter access on the gui object
    gui.medium_1_changed.connect(print)
    # we can connect a callback function to the __call__ event on the function
    gui.called.connect(lambda result: gui.set_widget("angle_of_refraction", result))
