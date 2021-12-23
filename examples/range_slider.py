from typing import Tuple
from magicgui import magicgui


@magicgui(range_value=dict(widget_type="RangeSlider"))
def func(range_value: Tuple[int, int] = (20, 80)):
    return range_value

func.show(run=True)
