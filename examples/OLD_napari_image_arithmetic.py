"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!
DEPRECATED!  DON'T USE THIS
!!!!!!!!!!!!!!!!!!!!!!!!!!!

This example is just here for aiding in migration to v0.2.0.
see examples/napari_image_arithmetic.py instead

"""
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
    viewer.add_image(numpy.random.rand(20, 20), name="Layer 1")
    viewer.add_image(numpy.random.rand(20, 20), name="Layer 2")

    # use the magic decorator!  This takes a function, generates a custom Widget class
    # using the function signature, and adds that class as an attribute named "Gui" on
    # the function.
    @magicgui(call_button="execute")
    def image_arithmetic(layerA: Image, operation: Operation, layerB: Image) -> Image:
        """Add, subtracts, multiplies, or divides to image layers with equal shape."""
        return operation.value(layerA.data, layerB.data)

    # Gui() is DEPRECATED
    # you should now just add the decorated function directly:
    # viewer.window.add_dock_widget(image_arithmetic)
    gui = image_arithmetic.Gui()
    viewer.window.add_dock_widget(gui.native)
    # NOTE: gui.native will not be necessary after
    # https://github.com/napari/napari/pull/1994

    # Use `reset_choices` instead now:
    # viewer.layers.events.inserted.connect(image_arithmetic.reset_choices)
    # viewer.layers.events.removed.connect(image_arithmetic.reset_choices)
    viewer.layers.events.inserted.connect(gui.refresh_choices)
    viewer.layers.events.removed.connect(gui.refresh_choices)
