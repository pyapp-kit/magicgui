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
    degrees=True,
    angle_of_incidence=30.0,
    medium_1=Medium.Glass,
    medium_2=Medium.Water,
    angle_of_refraction="...",
):
    n1 = medium_1.value
    n2 = medium_2.value
    if degrees:
        angle_of_incidence = math.radians(angle_of_incidence)
    try:
        result = math.asin(n1 * math.sin(angle_of_incidence) / n2)
        return round(math.degrees(result) if degrees else result, 2)
    except ValueError:  # math domain error
        return "TIR!"


with event_loop():
    print(snells_law())
    gui = snells_law.Gui(show=True)
    gui.called.connect(
        lambda result: gui.set_widget("angle_of_refraction", str(result))
    )
