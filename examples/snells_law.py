from enum import Enum
import math

from magicgui import event_loop, magicgui


# dropdown boxes are best made by creating an enum
class Medium(Enum):
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(call_button=True)
def snells_law(
    angle_of_incidence=30.0, medium_1=Medium.Glass, medium_2=Medium.Water, degrees=True
):
    n1 = Medium[medium_1].value
    n2 = Medium[medium_2].value
    if degrees:
        angle_of_incidence = math.radians(angle_of_incidence)
    try:
        result = math.asin(n1 * math.sin(angle_of_incidence) / n2)
        return math.degrees(result) if degrees else result
    except ValueError:  # math domain error
        return "Total internal reflection!"


with event_loop():
    # print(snells_law())
    gui = snells_law.show()
    gui.called.connect(lambda result: gui.set_widget("angle_of_refraction", result))
