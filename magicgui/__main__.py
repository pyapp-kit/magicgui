# For testing for now
from qtpy.QtWidgets import QApplication
from napari import Viewer, layers
import numpy
from enum import Enum
from magicgui.core import magicgui


class MyEnum(Enum):
    Oil = 1.515
    Water = 1.33
    Air = 1.0


running = True
app = QApplication.instance()
if not app:
    app = QApplication([])
    running = False

v = Viewer()
for i in range(2):
    v.add_image(numpy.random.rand(5, 5), name=f"Layer {i}")


@magicgui(
    layerA={"choices": v.layers},
    layerB={"choices": v.layers},
    method={"choices": ["+", "-", "x", "÷"]},
    call_button=True,
)
def test_function(layerA: layers.Layer, method: str, layerB: layers.Layer) -> None:
    """my docs"""
    layA = next(l for l in v.layers if l.name == layerA)
    layB = next(l for l in v.layers if l.name == layerB)
    func = getattr(
        numpy, {"+": "add", "-": "subtract", "x": "multiply", "'÷": "divide"}[method]
    )
    result = func(layA.data, layB.data)
    try:
        outlayer = next(l for l in v.layers if l.name == "output")
        outlayer.data = result
    except StopIteration:
        outlayer = v.add_image(data=result, name="output")
    return result


widget = test_function.Gui()
v.window.add_dock_widget(widget)


def update_choices(event=None):
    widget.layerA_widget.clear()
    widget.layerA_widget.addItems(map(str, v.layers))
    widget.layerB_widget.clear()
    widget.layerB_widget.addItems(map(str, v.layers))


v.layers.events.added.connect(update_choices)

if not running:
    app.exec_()
