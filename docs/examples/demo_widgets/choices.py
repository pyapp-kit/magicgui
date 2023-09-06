"""# Dropdown selection widget

Choices for dropdowns can be provided in a few different ways.
"""
from enum import Enum

from magicgui import magicgui, widgets


class Medium(Enum):
    """Enum for various media and their refractive indices."""

    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(ri={"choices": ["Oil", "Water", "Air"]}, auto_call=True)
def as_list(ri="Water"):
    """Function decorated with magicgui list of choices."""
    print("refractive index is", Medium[ri].value)


@magicgui(auto_call=True)
def as_enum(ri: Medium = Medium.Water):
    """Function decorated with magicgui and enumeration."""
    print("refractive index is", ri.value)


@magicgui(
    ri={"choices": [("Oil", 1.515), ("Water", 1.33), ("Air", 1.0)]}, auto_call=True
)
def as_2tuple(ri=1.33):
    """Function decorated with magicgui tuple of choices."""
    print("refractive index is", ri)


def get_choices(gui):
    """Function returning tuple of material and refractive index value."""
    return [("Oil", 1.515), ("Water", 1.33), ("Air", 1.0)]


@magicgui(ri={"choices": get_choices}, auto_call=True)
def as_function(ri: float):
    """Function to calculate refractive index."""
    print("refractive index is", ri)


container = widgets.Container(
    widgets=[as_list, as_enum, as_2tuple, as_function], layout="vertical"
)
container.show(run=True)
