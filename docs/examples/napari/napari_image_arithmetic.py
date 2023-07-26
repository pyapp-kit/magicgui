"""Basic example of using magicgui to create an Image Arithmetic GUI in napari."""
from enum import Enum

import napari
import numpy
from napari.layers import Image
from napari.types import ImageData

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


# create a viewer and add a couple image layers
viewer = napari.Viewer()
viewer.add_image(numpy.random.rand(20, 20), name="Layer 1")
viewer.add_image(numpy.random.rand(20, 20), name="Layer 2")


# for details on why the `-> ImageData` return annotation works:
# https://napari.org/guides/magicgui.html#return-annotations
@magicgui(call_button="execute", layout="horizontal")
def image_arithmetic(layerA: Image, operation: Operation, layerB: Image) -> ImageData:
    """Add, subtracts, multiplies, or divides to image layers with equal shape."""
    return operation.value(layerA.data, layerB.data)


# add our new magicgui widget to the viewer
viewer.window.add_dock_widget(image_arithmetic, area="bottom")


# note: the function may still be called directly as usual!
# new_image = image_arithmetic(img_a, Operation.add, img_b)

napari.run()
