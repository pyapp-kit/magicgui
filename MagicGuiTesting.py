from magicgui import magicgui
from enum import Enum
#test branch

class Medium(Enum):
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


# decorate your function with the @magicgui decorator
@magicgui(call_button="calculate", result_widget=True)
def snells_law(aoi=30.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
    import math

    aoi = math.radians(aoi) if degrees else aoi
    try:
        result = math.asin(n1.value * math.sin(aoi) / n2.value)
        return math.degrees(result) if degrees else result
    except ValueError:
        return "Total internal reflection!"


@magicgui(call_button="calculate", result_widget=True)
def long_calculation_test():
    summed = 0
    for _ in range(0, 10):
        for _ in range(0, 3000):
            for x in range(0, 10000):
                summed += x

    return summed


# your function is now capable of showing a GUI
# snells_law.show(run=True)
long_calculation_test.show(run=True)
