"""# napari parameter sweeps

[napari](https://github.com/napari/napari) is a fast, interactive,
multi-dimensional image viewer for python.  It uses Qt for the GUI, so it's easy
to extend napari with small, composable widgets created with `magicgui`.  Here,
we demonstrate how to build a interactive widget that lets you immediately see
the effect of changing one of the parameters of your function.

For napari-specific magicgui documentation, see the
[napari docs](https://napari.org/guides/magicgui.html)

![napari parameter sweep widget](../../images/param_sweep.gif){ width=80% }

*See also:* Some of this tutorial overlaps with topics covered in the
[napari image arithmetic example](napari_img_math.py).

## outline

**This example demonstrates how to:**

1. Create a `magicgui` widget that can be used in another
program (`napari`)

2. Automatically call our function when a parameter changes

3. Provide `magicgui` with a custom widget for a specific
argument

4. Use the `choices` option to create a dropdown

5. Connect some event listeners to create interactivity.

## code

*Code follows, with explanation below... You can also [get this example at
github](https://github.com/pyapp-kit/magicgui/blob/main/docs/examples/napari/napari_param_sweep.py).*

```python linenums="1" hl_lines="14-19 31"
import napari
import skimage.data
import skimage.filters
from napari.types import ImageData

from magicgui import magicgui


# turn the gaussian blur function into a magicgui
# - 'auto_call' tells magicgui to call the function when a parameter changes
# - we use 'widget_type' to override the default "float" widget on sigma,
#   and provide a maximum valid value.
# - we contstrain the possible choices for 'mode'
@magicgui(
    auto_call=True,
    sigma={"widget_type": "FloatSlider", "max": 6},
    mode={"choices": ["reflect", "constant", "nearest", "mirror", "wrap"]},
    layout="horizontal",
)
def gaussian_blur(layer: ImageData, sigma: float = 1.0, mode="nearest") -> ImageData:
    # Apply a gaussian blur to 'layer'.
    if layer is not None:
        return skimage.filters.gaussian(layer, sigma=sigma, mode=mode)

# create a viewer and add some images
viewer = napari.Viewer()
viewer.add_image(skimage.data.astronaut().mean(-1), name="astronaut")
viewer.add_image(skimage.data.grass().astype("float"), name="grass")

# Add it to the napari viewer
viewer.window.add_dock_widget(gaussian_blur)
# update the layer dropdown menu when the layer list changes
viewer.layers.events.changed.connect(gaussian_blur.reset_choices)

napari.run()
```

## walkthrough

We're going to go a little out of order so that the other code makes more sense.
Let's start with the actual function we'd like to write to apply a gaussian
filter to an image.

### the function

Our function is a very thin wrapper around
[`skimage.filters.gaussian`](https://scikit-image.org/docs/dev/api/skimage.filters.html#skimage.filters.gaussian).
It takes a `napari` [Image
layer](https://napari.org/howtos/layers/image.html), a `sigma` to control
the blur radius, and a `mode` that determines how edges are handled.

```python
def gaussian_blur(
    layer: Image, sigma: float = 1, mode="nearest"
) -> Image:
    return filters.gaussian(layer.data, sigma=sigma, mode=mode)
```

The reasons we are wrapping it here are:

1. `filters.gaussian` accepts a `numpy` array,
   but we want to work with `napari` layers
   that store the data in a `layer.data` attribute. So we need an adapter.
2. We'd like to add some [type annotations](../../type_map.md) to the
   signature that were not provided by `filters.gaussian`

#### type annotations

As described in the [image arithmetic example](napari_img_math.py), we take
advantage of napari's built in support for `magicgui` by annotating our function
parameters and return value as napari `Layer` types.  `napari` will then tell
`magicgui` what to do with them, creating a dropdown with a list of current
layers for our `layer` parameter, and automatically adding the result of our
function to the viewer when called.

For documentation on napari types with magicgui, see the
[napari docs](https://napari.org/guides/magicgui.html)

### the magic part

Finally, we decorate the function with `@magicgui` and provide some options.

```python
@magicgui(
    auto_call=True,
    sigma={"widget_type": "FloatSlider", "max": 6},
    mode={"choices": ["reflect", "constant", "nearest", "mirror", "wrap"]},
)
def gaussian_blur(
  layer: ImageData, sigma: float = 1.0, mode="nearest"
) -> ImageData:
    # Apply a gaussian blur to ``layer``.
    if layer is not None:
        return skimage.filters.gaussian(layer, sigma=sigma, mode=mode)
```

- `auto_call=True` makes it so that the `gaussian_blur` function will be called
  whenever one of the parameters changes (with the current parameters set in the
  GUI).
- We then provide keyword arguments to modify the look & behavior of `sigma`
  and `mode`:

    - `"widget_type": "FloatSlider"` tells `magicgui` not to use the standard
        (`float`) widget for the `sigma` widget, but rather to use a slider widget.
    - we then set an upper limit on the slider values for `sigma`.

- finally, we specify valid `choices` for the `mode` argument.  This turns that
  parameter into a categorical/dropdown type widget, and sets the options.

### connecting events

As described in the [Events documentation](../../events.md), we can
also connect any callback to the `gaussian_blur.called` signal that will receive
the result of our decorated function anytime it is called.

```python
def do_something_with_result(result):
    ...

gaussian_blur.called.connect(do_something_with_result)
```

## Code

Here's the full code example again.
"""

# %%
import napari
import skimage.data
import skimage.filters
from napari.types import ImageData

from magicgui import magicgui


# turn the gaussian blur function into a magicgui
# - 'auto_call' tells magicgui to call the function when a parameter changes
# - we use 'widget_type' to override the default "float" widget on sigma,
#   and provide a maximum valid value.
# - we contstrain the possible choices for 'mode'
@magicgui(
    auto_call=True,
    sigma={"widget_type": "FloatSlider", "max": 6},
    mode={"choices": ["reflect", "constant", "nearest", "mirror", "wrap"]},
    layout="horizontal",
)
def gaussian_blur(layer: ImageData, sigma: float = 1.0, mode="nearest") -> ImageData:
    # Apply a gaussian blur to 'layer'.
    if layer is not None:
        return skimage.filters.gaussian(layer, sigma=sigma, mode=mode)


# create a viewer and add some images
viewer = napari.Viewer()
viewer.add_image(skimage.data.astronaut().mean(-1), name="astronaut")
viewer.add_image(skimage.data.grass().astype("float"), name="grass")

# Add it to the napari viewer
viewer.window.add_dock_widget(gaussian_blur)
# update the layer dropdown menu when the layer list changes
viewer.layers.events.changed.connect(gaussian_blur.reset_choices)

napari.run()
