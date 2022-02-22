from magicgui import Field, GUIModel
from magicgui.widgets import Slider


class MyWidget(GUIModel):
    x: int = 1
    y: int = Field(2, ui_widget_type=Slider)


widget = MyWidget()
widget.gui.show(run=True)
