"""Basic example of using magicgui to create an Image Arithmetic GUI in napari."""
from enum import Enum

import numpy
from napari import Viewer, gui_qt
from napari.layers import Image

from magicgui import magicgui


class Operation(Enum):
    """A set of valid arithmetic operations for image_arithmetic.

    To create nice dropdown menus with magicgui, it's best (but not required) to use
    Enums.  Here we make an Enum class for all of the image math operations we want to
    allow.
    """

    add = numpy.add
    subtract = numpy.subtract
    multiply = numpy.multiply
    divide = numpy.divide


with gui_qt():
    # create a viewer and add a couple image layers
    viewer = Viewer()
    viewer.add_image(numpy.random.rand(20, 20), name=f"Layer 1")
    viewer.add_image(numpy.random.rand(20, 20), name=f"Layer 2")

    # use the magic decorator!  This takes a function, generates a custom Widget class
    # using the function signature, and adds that class as an attribute named "Gui" on
    # the function.
    @magicgui(call_button="execute")
    def image_arithmetic(layerA: Image, operation: Operation, layerB: Image) -> Image:
        """Add, subtracts, multiplies, or divides to image layers with equal shape."""
        return operation.value(layerA.data, layerB.data)

    # instantiate the widget
    gui = image_arithmetic.Gui()
    # add our new magicgui widget to the viewer
    viewer.window.add_dock_widget(gui.native)
    # keep the dropdown menus in the gui in sync with the layer model
    viewer.layers.events.inserted.connect(gui.refresh_choices)
    viewer.layers.events.removed.connect(gui.refresh_choices)

    # Bonus:

    # there is two way binding between the data widgets in the gui and the attribute of
    # the same name on the gui instance:
    gui.operation = Operation.multiply  # changes the gui as well
