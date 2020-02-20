"""Basic example of using magicgui to create an Image Arithmetic GUI in napari."""
from enum import Enum

import numpy

from magicgui import magicgui, register_type
from napari import Viewer, gui_qt, layers


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


# we're going to let magicgui know how to render one of our custom types (layers.Layer)
#
# the `register_types` function below accepts a type, and either a `widget_type`
# OR a `choices` argument (choices takes precendence).
#
# If `widget_type` is provided, it must be a valid widget class for the gui backed
# (e.g. QWidget).  If `choices` is provided, the widget is assumed to be a dropdown box.
# `choices` must either be an iterable, or a callable.
#
# If it is a callable, it will be called with the type of the function parameter being
# rendered. In this case, we want any subclass of layers.Layer to be rendered as a
# dropdown, but we only want layers of the type specified in the type hint to be shown.
def get_layer_choices(gui, layer_type):
    try:
        # look for the parent Viewer based on where the magicgui is docked.
        # if the magicgui widget does not have a parent, it is unattached
        # to any viewers, and therefore we cannot return a list of layers
        viewer = gui.parent().qt_viewer.viewer
        return tuple(l for l in viewer.layers if isinstance(l, layer_type))
    except AttributeError:
        return ()


def show_result(gui, result):
    """Show result of image_arithmetic in viewer."""
    try:
        viewer = gui.parent().qt_viewer.viewer
    except AttributeError:
        viewer = None

    if viewer and (result is not None):
        try:
            viewer.layers["result"].data = result
        except KeyError:
            viewer.add_image(data=result, name="result")


register_type(layers.Layer, choices=get_layer_choices, return_callback=show_result)


with gui_qt():
    # create a viewer and add a couple image layers
    viewer = Viewer()
    viewer.add_shapes(20 * numpy.random.random((5, 4, 2)), name="Shapes")
    viewer.add_image(numpy.random.rand(20, 20), name=f"Layer 1")
    viewer.add_image(numpy.random.rand(20, 20), name=f"Layer 2")

    # use the magic decorator!  This takes a function, generates a custom Widget class
    # using the function signature, and adds that class as an attribute called "Gui" on
    # the function.
    @magicgui(call_button="execute")
    def image_arithmetic(
        layerA: layers.Image, operation: Operation, layerB: layers.Image
    ) -> layers.Layer:
        """Add, subtracts, multiplies, or divides to image layers with equal shape."""
        return operation.value(layerA.data, layerB.data)

    # instantiate the widget
    gui = image_arithmetic.Gui()
    # parentChanged is a special signal set on MagicGui classes in the Qt backend
    # we use it here to update the layer choices when the widget is docked in a viewer.
    gui.parentChanged.connect(gui.refresh_choices)

    # add our new magicgui widget to the viewer
    viewer.window.add_dock_widget(gui)

    # notice how the dropdowns only show the current image layers... not the shapes.
    # that is because of how we used `register_type` above.

    # keep the dropdown menus in the gui in sync with the layer model
    viewer.layers.events.added.connect(lambda x: gui.refresh_choices())
    viewer.layers.events.removed.connect(lambda x: gui.refresh_choices())

    # Bonus:

    # there is two way binding between the data widgets in the gui and the attribute of
    # the same name on the gui instance:
    gui.operation = Operation.multiply  # changes the gui as well

    # the original function is still functional.  It can be called with the
    # original function signature with arguments. HOWEVER, the "default" values for the
    # function stay in sync with the GUI.  So as the user changes the values in the gui:
    # calling the original function will give results as if the gui values were provided

    # image_arithmetic()

    # lastly, if you DO provide arguments to the original function call, they will
    # override those provided by the GUI (note: the GUI will not change though unless
    # you explicitly set those values as mentioned above)

    # image_arithmetic(operation=Operation.divide)
