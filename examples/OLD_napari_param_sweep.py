"""
!!!!!!!!!!!!!!!!!!!!!!!!!!!
DEPRECATED!  DON'T USE THIS
!!!!!!!!!!!!!!!!!!!!!!!!!!!

This example is just here for aiding in migration to v0.2.0.
see examples/napari_param_sweep.py instead

"""
import napari
import skimage.data
import skimage.filters
from napari.layers import Image

from magicgui import magicgui

# REMOVED! use string 'FloatSlider' instead
from magicgui._qt.widgets import QDoubleSlider

with napari.gui_qt():
    # create a viewer and add some images
    viewer = napari.Viewer()
    viewer.add_image(skimage.data.astronaut().mean(-1), name="astronaut")
    viewer.add_image(skimage.data.grass().astype("float"), name="grass")

    @magicgui(
        auto_call=True,
        # "fixedWidth" is qt specific and no longer works
        # this will eventually raise an exception
        sigma={"widget_type": QDoubleSlider, "max": 6, "fixedWidth": 400},
        mode={"choices": ["reflect", "constant", "nearest", "mirror", "wrap"]},
    )
    def gaussian_blur(layer: Image, sigma: float = 1.0, mode="nearest") -> Image:
        """Apply a gaussian blur to ``layer``."""
        if layer:
            return skimage.filters.gaussian(layer.data, sigma=sigma, mode=mode)

    # DEPRECATED: you no longer should use Gui()...
    # just use `gaussian_blur` directly (it's already a magicgui widget)
    gui = gaussian_blur.Gui()

    # should now just be viewer.window.add_dock_widget(gaussian_blur)
    viewer.window.add_dock_widget(gui)

    # Should now be: viewer.layers.events.changed.connect(gaussian_blur.reset_choices)
    viewer.layers.events.changed.connect(lambda x: gui.refresh_choices("layer"))
