"""Example showing how to accomplish a napari parameter sweep with magicgui.

It demonstrates:
1. overriding the default widget type with a custom class
2. the `auto_call` option, which calls the function whenever a parameter changes

"""
from magicgui import magicgui
from magicgui._qt import QDoubleSlider
from napari import Viewer, gui_qt, layers
from skimage import data, filters


with gui_qt():
    # create a viewer and add some images
    viewer = Viewer()
    viewer.add_image(data.astronaut().mean(-1), name="astronaut")
    viewer.add_image(data.grass().astype("float"), name="grass")

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
        """Apply a gaussian blur to ``layer``."""
        if layer:
            return filters.gaussian(layer.data, sigma=sigma, mode=mode)

    # instantiate the widget
    gui = gaussian_blur.Gui()
    gui.parentChanged.connect(gui.refresh_choices)

    def show_result(result):
        """Show result of image_arithmetic in viewer."""
        if result is not None:
            try:
                viewer.layers["blurred"].data = result
            except KeyError:
                viewer.add_image(data=result, name="blurred")

    gaussian_blur.called.connect(show_result)
    viewer.window.add_dock_widget(gui)
    viewer.layers.events.added.connect(lambda x: gui.refresh_choices("layer"))
    viewer.layers.events.removed.connect(lambda x: gui.refresh_choices("layer"))
