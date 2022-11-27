from typing import Tuple

from magicgui import magicgui


@magicgui(auto_call=True, range_value={"widget_type": "RangeSlider", "max": 500})
def func(range_value: Tuple[int, int] = (20, 380)):
    print(range_value)


func.show(run=True)
