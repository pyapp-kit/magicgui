"""Widget demonstration of magicgui."""

import datetime
from enum import Enum
from pathlib import Path

from magicgui import magicgui


class Medium(Enum):
    """Enum for various media and their refractive indices."""

    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(
    main_window=True,
    call_button="Calculate",
    layout="vertical",
    result_widget=True,
    slider_float={"widget_type": "FloatSlider"},
    filename={"label": "Pick a file:"},
)
def widget_demo(
    boolean=True,
    integer=1,
    spin_float=3.14159,
    slider_float=4.5,
    string="Text goes here",
    dropdown=Medium.Glass,
    date=datetime.date(1999, 12, 31),
    time=datetime.time(1, 30, 20),
    datetime=datetime.datetime.now(),
    filename=Path.home(),
):
    """We can use numpy docstrings to provide tooltips.

    Parameters
    ----------
    boolean : bool, optional
        A checkbox for booleans, by default True
    integer : int, optional
        Some integer, by default 1
    spin_float : float, optional
        This one is a float, by default "pi"
    slider_float : float, optional
        Hey look! I'm a slider, by default 4.5
    string : str, optional
        We'll use this string carefully, by default "Text goes here"
    dropdown : Enum, optional
        Pick a medium, by default Medium.Glass
    date : datetime.date, optional
        Your birthday, by default datetime.date(1999, 12, 31)
    time : datetime.time, optional
        Some time, by default datetime.time(1, 30, 20)
    datetime : datetime.datetime, optional
        A very specific time and date, by default ``datetime.datetime.now()``
    filename : str, optional
        Pick a path, by default Path.home()
    """
    return locals().values()


widget_demo.changed.connect(lambda event: print(widget_demo))
widget_demo.show(run=True)
