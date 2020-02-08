from enum import Enum

import numpy

from magicgui import magicgui
from napari import Viewer, gui_qt, layers

with gui_qt():
    viewer = Viewer()
    viewer.add_image(numpy.random.rand(10, 10), name=f"Layer 1")
    viewer.add_image(numpy.random.rand(10, 10), name=f"Layer 2")

    class ImageMathMethod(Enum):
        add = numpy.add
        subtract = numpy.subtract
        multiply = numpy.multiply
        divide = numpy.divide

    @magicgui(
        layerA={"choices": viewer.layers},
        layerB={"choices": viewer.layers},
        call_button="execute",
    )
    def image_arithmetic(
        layerA: layers.Layer, method: ImageMathMethod, layerB: layers.Layer
    ) -> None:
        """Adds, subtracts, multiplies, or divides to image layers with equal shape."""
        return method.value(layerA.data, layerB.data)

    def show_result(result):
        # put the result into a new layer called "output" or overwrite if one exists.
        try:
            outlayer = next(l for l in viewer.layers if l.name == "result")
            outlayer.data = result
        except StopIteration:
            outlayer = viewer.add_image(data=result, name="result")

    gui = image_arithmetic.Gui()
    gui.called.connect(show_result)
    viewer.window.add_dock_widget(gui)
    viewer.layers.events.added.connect(
        lambda x: gui.set_choices("layerA", viewer.layers)
    )
    viewer.layers.events.added.connect(
        lambda x: gui.set_choices("layerB", viewer.layers)
    )
