"""Simple demonstration of magicgui."""

import math
from enum import Enum

from magicgui import magicgui


class Medium(Enum):
    """Enum for various media and their refractive indices."""

    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(call_button="calculate", result_widget=True)
def snells_law(aoi=1.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
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


snells_law.show(run=True)
