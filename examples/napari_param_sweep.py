"""Example showing how to accomplish a napari parameter sweep with magicgui.

It demonstrates:
1. overriding the default widget type with a custom class
2. the `auto_call` option, which calls the function whenever a parameter changes

"""
import napari
import skimage.data
import skimage.filters
from napari.layers import Image
from napari.types import ImageData

from magicgui import magicgui

# create a viewer and add some images
viewer = napari.Viewer()
viewer.add_image(skimage.data.astronaut().mean(-1), name="astronaut")
viewer.add_image(skimage.data.grass().astype("float"), name="grass")


# turn the gaussian blur function into a magicgui
# for details on why the `-> ImageData` return annotation works:
# https://napari.org/guides/magicgui.html#return-annotations
@magicgui(
    # tells magicgui to call the function whenever a parameter changes
    auto_call=True,
    # `widget_type` to override the default (spinbox) "float" widget
    sigma={"widget_type": "FloatSlider", "max": 6},
    # contstrain the possible choices for `mode`
    mode={"choices": ["reflect", "constant", "nearest", "mirror", "wrap"]},
    layout="horizontal",
)
def gaussian_blur(layer: Image, sigma: float = 1.0, mode="nearest") -> ImageData:
    """Apply a gaussian blur to ``layer``."""
    if layer:
        return skimage.filters.gaussian(layer.data, sigma=sigma, mode=mode)


# Add it to the napari viewer
viewer.window.add_dock_widget(gaussian_blur, area="bottom")

napari.run()
