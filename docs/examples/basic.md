# Basic Widget Demo

This code demonstrates a few of the widget types that magicgui can
create based on the parameter types in your function

```python
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
    # them sliders using the 'widget_type' option
    slider_float={"widget_type": "FloatSlider", "max": 100},
    slider_int={"widget_type": "Slider", "readout": False},
    radio_option={
        "widget_type": "RadioButtons",
        "orientation": "horizontal",
        "choices": [("first option", 1), ("second option", 2)],
    },
    filename={"label": "Pick a file:"},  # custom label
)
def widget_demo(
    boolean=True,
    integer=1,
    spin_float=3.14159,
    slider_float=43.5,
    slider_int=550,
    string="Text goes here",
    dropdown=Medium.Glass,
    radio_option=2,
    date=datetime.date(1999, 12, 31),
    time=datetime.time(1, 30, 20),
    datetime=datetime.datetime.now(),
    filename=Path.home(),  # path objects are provided a file picker
):
    """Run some computation."""
    return locals().values()

widget_demo.show()
```
