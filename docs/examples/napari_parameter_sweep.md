# napari parameter sweeps

[napari](https://github.com/napari/napari) is a fast, interactive, multi-dimensional
image viewer for python.  It uses Qt for the GUI, so it's easy to extend napari with
small, composable widgets created with `magicgui`.  Here, we demonstrate how to build a
interactive widget that lets you immediately see the effect of changing one of the
parameters of your function.

<p align="center"><img src="../../img/param_sweep.gif" width="80%" /></p>

*See also: *Some of this tutorial overlaps with topics covered in the [napari image arithmetic
example](napari_img_math.md)

## outline

**This example demonstrates how to:**

[⬇️](#the-magic-part) Create a `magicgui` widget that can be used in another
program (`napari`)

[⬇️](#the-magic-part) Automatically call our function when a parameter changes

[⬇️](#custom-widgets) Provide `magicgui` with a custom widget for a specific
argument

[⬇️](#the-magic-part) Use the `choices` option to create a dropdown


[⬇️](#connecting-events) Connect some event listeners to create interactivity.

## code

*Code follows, with explanation below... You can also [get this example at github](
https://github.com/napari/magicgui/blob/master/examples/napari_param_sweep.py).*

???+ example "complete code"

    ```python hl_lines="19 20 21 22 23 30 32 34"
    from magicgui import magicgui
    from magicgui._qt import QDoubleSlider
    import napari
    from napari.layers import Image
    import skimage

    ######   THIS SECTION ONLY REQUIRED FOR NAPARI <= 0.2.12   ######

    with napari.gui_qt():
        # create a viewer and add some images
        viewer = napari.Viewer()
        viewer.add_image(skimage.data.astronaut().mean(-1), name="astronaut")
        viewer.add_image(skimage.data.grass().astype('float'), name="grass")

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
        def gaussian_blur(layer: Image, sigma: float = 1.0, mode="nearest") -> Image:
            """Apply a gaussian blur to ``layer``."""
            if layer:
                return skimage.filters.gaussian(layer.data, sigma=sigma, mode=mode)

        # instantiate the widget
        gui = gaussian_blur.Gui()
        # add the gui to the viewer as a dock widget
        viewer.window.add_dock_widget(gui)
        # if a layer gets added or removed, refresh the dropdown choices
        viewer.layers.events.changed.connect(lambda x: gui.refresh_choices("layer"))
    ```

## walkthrough

We're going to go a little out of order so that the other code makes more sense.  Let's
start with the actual function we'd like to write to apply a gaussian filter to an image.

### the function

Our function is a very thin wrapper around
[`skimage.filters.gaussian`](https://scikit-image.org/docs/dev/api/skimage.filters.html#skimage.filters.gaussian).
It takes a `napari` [Image layer](https://napari.org/tutorials/fundamentals/image), a
`sigma` to control the blur radius, and a `mode` that determines how edges are handled.

```python
def gaussian_blur(layer: Image, sigma: float = 1, mode="nearest") -> Image:
    return filters.gaussian(layer.data, sigma=sigma, mode=mode)
```

The reasons we are wrapping it here are:

1. `filters.gaussian` accepts a `numpy` array, but we want to work with `napari` layers
   that store the data in a `layer.data` attribute. So we need an adapter.
2. We'd like to add some [type annotations](../type_inference.md#type-inference) to the
   signature that were not provided by `filters.gaussian`

*Note: a later tutorial will demonstrate how to use
[wrapt](https://github.com/GrahamDumpleton/wrapt) to adapt functions like this in more
automated way*

#### type annotations

As described in the [image arithmetic
tutorial](../napari_img_math/#connect-event-listeners-for-interactivity), we
take advantage of napari's built in support for `magicgui` by annotating our
function parameters and return value as napari `Layer` types.  `napari` will
then tell `magicgui` what to do with them, creating a dropdown with a list of
current layers for our `layer` parameter, and automatically adding the result of
our function to the viewer when called.

### the magic part

Finally, we decorate the function with `@magicgui` and provide some options.

```python hl_lines="1 2 3 4 5"
@magicgui(
    auto_call=True,
    sigma={"widget_type": QDoubleSlider, "maximum": 6, "fixedWidth": 400},
    mode={"choices": ["reflect", "constant", "nearest", "mirror", "wrap"]},
)
def gaussian_blur(layer: Image, sigma: float = 1., mode="nearest") -> Image:
    if layer:
        return filters.gaussian(layer.data, sigma=sigma, mode=mode)
```

- `auto_call=True` makes it so that the `gaussian_blur` function will be called
  with the current parameters set in the GUI whenever one of the parameters
  changes.
- We then use
  [argument-specific](../../configuration/#argument-specific-options) parameters
  to modify the look & behavior of `sigma` and `mode`:
    * `"widget_type": QDoubleSlider` tells `magicgui` not to use the standard
        (`float`) widget for the `sigma` widget, but rather to use a custom widget
        type.  This one comes built in with `magicgui`, but you are also welcome
        to build your own if you do know some Qt.
    * we then set a couple [Qt-specific
        options](../../configuration/#qt-specific-options) on `sigma`, that will
        directly call the `setMaximum()` (to set an upper limit on the slider
        values) and `setFixedWidth()` methods (to control the width of the
        slider).
- finally, we specify valid `choices` for the `mode` argument.  This turns that
  parameter into a categorical/dropdown type widget, and sets the options.

The `gaussian_blur` function now has an attribute `gaussian_blur.Gui` that we can call to
instantiate our GUI.

```python
# instantiate the widget
gui = gaussian_blur.Gui()
```

### custom widgets

If you *do* know some Qt for python programming and would like to provide custom
widgets for certain arguments this can be done in an argument-specific way, by
providing the `widget_type` option in one of the argument-specific options
`dict`s.  We do that here for the `sigma` parameter, directing it the custom
`QDoubleSlider` class from `magicgui._qt`. If you're curious, here's what that
class looks like:

```python
from qtpy import QtWidgets, QtCore

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
```

We could also have registered this slider widget globally for *all* `float` type
variables using the `magicgui.register_type` function:

```python
from magicgui import register_type

register_type(float, widget_type=QDoubleSlider)
```

See [`register_type`](../../type_inference/#register_type) for usage details.

### connecting events

As described in the [image arithmetic
tutorial](../napari_img_math/#connect-event-listeners-for-interactivity), we can
also connect any callback to the `gaussian_blur.called` signal that will receive
the result of our decorated function anytime it is called.

```python
gaussian_blur.called.connect(do_something_with_result)
```
