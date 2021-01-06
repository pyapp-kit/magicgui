---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.12
    jupytext_version: 1.7.1
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# basic widget demo

This code demonstrates a few of the widget types that magicgui can
create based on the parameter types in your function

```{code-cell} python
import datetime
from enum import Enum
from pathlib import Path

from magicgui import magicgui


class Medium(Enum):
    """Using Enums is a great way to make a dropdown menu."""
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(
    call_button="Calculate",
    layout="vertical",
    result_widget=True,
    # numbers default to spinbox widgets, but we can make
    # them sliders using the `widget_type` option
    slider_float={"widget_type": "FloatSlider"},
    filename={"label": "Pick a file:"},  # custom label
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
    filename=Path.home(),  # path objects are provided a file picker
):
    """Run some computation."""
    return locals().values()

widget_demo.show() # if running locally, use `show(run=True)`
```
