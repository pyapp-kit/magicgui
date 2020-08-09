"""Simple demonstration of magicgui."""

from enum import Enum
import math

from magicgui.signature import magic_signature
from magicgui import event_loop
from typing_extensions import Annotated


class Medium(Enum):
    """Enum for various media and their refractive indices."""

    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


def choices(obj):
    print(obj.name, obj.annotation)
    return ["a", "b", "c"]


# @magicgui(call_button="calculate", result={"disabled": True, "fixedWidth": 100})
def snells_law(
    aoi=30.0,
    n1=Medium.Glass,
    n2=Medium.Water,
    b: Annotated[str, {"choices": choices}] = "c",
    degrees=True,
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
    ms = magic_signature(snells_law)
    w = ms.to_container()
    print(w)
    print(w.to_signature())
    w.show()

