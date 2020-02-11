"""
This example shows how to accomplish a parameter sweep with magicgui.  It demonstrates:
1. overriding the default widget type with a custom class
2. the `auto_call` option, which calls the function whenever a parameter changes

"""
from magicgui import magicgui, register_type
from napari import Viewer, gui_qt, layers
from skimage import data, filters
from qtpy import QtWidgets, QtCore


def get_layers(layer_type):
    return tuple(l for l in viewer.layers if isinstance(l, layer_type))


register_type(layers.Layer, choices=get_layers)


# Qt Doesn't have a built in class for float sliders
class QDoubleSlider(QtWidgets.QSlider):
    PRECISION = 1000

    def __init__(self, parent=None):
        super().__init__(QtCore.Qt.Horizontal, parent=parent)

    def value(self):
        return super().value() / self.PRECISION

    def setValue(self, value):
        super().setValue(value * self.PRECISION)

    def setMaximum(self, value):
        super().setMaximum(value * self.PRECISION)


with gui_qt():
    # create a viewer and add some images
    viewer = Viewer()
    viewer.add_image(data.astronaut().mean(-1), name="astronaut")
    viewer.add_image(data.grass().astype('float'), name="grass")

    # turn the gaussian blur function into a magicgui
    # - `auto_call` tells magicgui to call the function whenever a parameter changes 
    # - we use `widget_type` to override the default "float" widget on sigma
    # - we provide some Qt-specific parameters
    # - we contstrain the possible choices for `mode`
    @magicgui(
        auto_call=True,
        sigma={"widget_type": QDoubleSlider, "maximum": 6, "fixedWidth": 400},
        mode={"choices": ["reflect", "constant", "nearest", "mirror", "wrap"]},
    )
    def gaussian_blur(layer: layers.Image, sigma: float = 1, mode="nearest") -> None:
        return filters.gaussian(layer.data, sigma=sigma, mode=mode)

    # instantiate the widget
    gui = gaussian_blur.Gui()

    def show_result(result):
        """callback function for whenever the image_arithmetic functions is called"""
        try:
            viewer.layers["result"].data = result
        except KeyError:
            viewer.add_image(data=result, name="blurred")

    gaussian_blur.called.connect(show_result)
    viewer.window.add_dock_widget(gui)
    viewer.layers.events.added.connect(lambda x: gui.fetch_choices("layer"))
    viewer.layers.events.removed.connect(lambda x: gui.fetch_choices("layer"))
