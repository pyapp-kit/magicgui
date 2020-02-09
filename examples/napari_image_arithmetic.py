from enum import Enum

import numpy

from magicgui import magicgui
from napari import Viewer, gui_qt, layers


class Operation(Enum):
    """To create nice dropdown menus with magicgui, it's best (but not required) to use
    Enums.  here we make an Enum class for all of the image math operations we want to
    allow."""
    add = numpy.add
    subtract = numpy.subtract
    multiply = numpy.multiply
    divide = numpy.divide


with gui_qt():
    # create a viewer and add a couple image layers
    viewer = Viewer()
    viewer.add_image(numpy.random.rand(10, 10), name=f"Layer 1")
    viewer.add_image(numpy.random.rand(10, 10), name=f"Layer 2")

    # use the magic decorator!  This takes a function, generates a custom Widget class
    # using the function signature, and adds that class as an attribute called "Gui" on
    # the function.  The decorator also takes some (optional) arguments.
    @magicgui(
        layerA={"choices": viewer.layers},
        layerB={"choices": viewer.layers},
        call_button="execute",
    )
    def image_arithmetic(
        layerA: layers.Layer, operation: Operation, layerB: layers.Layer
    ) -> None:
        """Adds, subtracts, multiplies, or divides to image layers with equal shape."""
        return operation.value(layerA.data, layerB.data)

    def show_result(result):
        """callback function for whenever the image_arithmetic functions is called"""
        try:
            outlayer = viewer.layers["result"]
            outlayer.data = result
        except KeyError:
            outlayer = viewer.add_image(data=result, name="result")

    # instantiate the widget
    gui = image_arithmetic.Gui()
    # the function also acquires a signal that is emitted whenever it is called
    # it receives the results of the function and can be hooked to any callback
    # (note, this signal also lives at `gui.called`)
    image_arithmetic.called.connect(show_result)
    # add our new magicgui widget to the viewer
    viewer.window.add_dock_widget(gui)

    # keep the dropdown menus in the gui in sync with the layer model
    viewer.layers.events.added.connect(
        lambda x: gui.set_choices("layerA", viewer.layers)
    )
    viewer.layers.events.added.connect(
        lambda x: gui.set_choices("layerB", viewer.layers)
    )
    viewer.layers.events.removed.connect(
        lambda x: gui.set_choices("layerA", viewer.layers)
    )
    viewer.layers.events.removed.connect(
        lambda x: gui.set_choices("layerB", viewer.layers)
    )

    # Bonus:
    