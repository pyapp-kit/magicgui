from enum import auto

from pydantic.types import conint

from magicgui import magicgui


@magicgui(auto_call=True, x={"widget_type": "Slider"})
def t(x: conint(ge=100, le=200) = 150):
    print(x)


t.show(run=True)
