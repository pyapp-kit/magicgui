"""# napari image arithmetic widget

[napari](https://github.com/napari/napari) is a fast, interactive,
multi-dimensional image viewer for python.  It uses Qt for the GUI, so it's easy
to extend napari with small, composable widgets created with `magicgui`.  Here
we're going to build this simple image arithmetic widget with a few additional
lines of code.

For napari-specific magicgui documentation, see the [napari
docs](https://napari.org/guides/magicgui.html)

![napari image arithmetic widget](../../images/imagemath.gif){ width=80% }

## outline

**This example demonstrates how to:**

1. Create a `magicgui` widget that can be used in another program (napari)

2. Use an `Enum` to create a dropdown menu

3. Connect some event listeners to create interactivity.

## code

*Code follows, with explanation below... You can also [get this example at
github](https://github.com/pyapp-kit/magicgui/blob/main/docs/examples/napari/napari_image_arithmetic.py).*

```python linenums="1" hl_lines="25 38"
from enum import Enum

import napari
import numpy
from napari.types import ImageData

from magicgui import magicgui


class Operation(Enum):
    # A set of valid arithmetic operations for image_arithmetic.
    #
    # To create nice dropdown menus with magicgui, it's best
    # (but not required) to use Enums.  Here we make an Enum
    # class for all of the image math operations we want to
    # allow.
    add = numpy.add
    subtract = numpy.subtract
    multiply = numpy.multiply
    divide = numpy.divide


# here's the magicgui!  We also use the additional
# `call_button` option
@magicgui(call_button="execute")
def image_arithmetic(
    layerA: ImageData, operation: Operation, layerB: ImageData
) -> ImageData:
    # Add, subtracts, multiplies, or divides to image layers.
    return operation.value(layerA, layerB)

# create a viewer and add a couple image layers
viewer = napari.Viewer()
viewer.add_image(numpy.random.rand(20, 20), name="Layer 1")
viewer.add_image(numpy.random.rand(20, 20), name="Layer 2")

# add our new magicgui widget to the viewer
viewer.window.add_dock_widget(image_arithmetic)

# keep the dropdown menus in the gui in sync with the layer model
viewer.layers.events.inserted.connect(image_arithmetic.reset_choices)
viewer.layers.events.removed.connect(image_arithmetic.reset_choices)

napari.run()
```

## walkthrough

We're going to go a little out of order so that the other code makes more sense.
Let's start with the actual function we'd like to write to do some image arithmetic.

### the function

Our function takes two `numpy` arrays (in this case, from [Image layers](https://napari.org/howtos/layers/image.html)),
and some mathematical operation
(we'll restrict the options using an `enum.Enum`).
When called, ourfunction calls the selected operation on the data.

```python
def image_arithmetic(array1, operation, array2):
    return operation.value(array1, array2)
```

#### type annotations

`magicgui` works particularly well with [type annotations](https://docs.python.org/3/library/typing.html),
and allows third-party libraries to register widgets and behavior for handling
their custom types (using [`magicgui.type_map.register_type`][magicgui.type_map.register_type]).
`napari` [provides support for `magicgui`](https://github.com/napari/napari/blob/main/napari/utils/_magicgui.py)
by registering a dropdown menu whenever a function parameter is annotated as one
of the basic napari [`Layer` types](https://napari.org/howtos/layers/index.html),
or, in this case, `ImageData` indicates we just the `data` attribute of the layer.
Furthermore, it recognizes when a function has a `napari.layers.Layer`
or `LayerData` return type annotation, and will add the result to the viewer.
So we gain a *lot* by annotating the above function with the appropriate
`napari` types.

```python
from napari.types import ImageData

def image_arithmetic(
    layerA: ImageData, operation: Operation, layerB: ImageData
) -> ImageData:
    return operation.value(layerA, layerB)
```

### the magic part

Finally, we decorate the function with `@magicgui` and tell it we'd like to
have a `call_button` that we can click to execute the function.

```python hl_lines="1"
@magicgui(call_button="execute")
def image_arithmetic(layerA: ImageData, operation: Operation, layerB: ImageData):
    return operation.value(layerA, layerB)
```

That's it!  The `image_arithmetic` function is now a
[FunctionGui][magicgui.widgets.FunctionGui] that can be shown, or incorporated
into other GUIs (such as the napari GUI shown in this example)

!!! note While [type hints](https://docs.python.org/3/library/typing.html)
    aren't always required in `magicgui`, they are recommended ... and they
    *are* required for certain things, like the `Operation(Enum)` [used here for
    the dropdown](#create-dropdowns-with-enums) and the `napari.types.ImageData`
    annotations that `napari` has registered with `magicgui`.

### create dropdowns with Enums

We'd like the user to be able to select the operation (`add`, `subtract`,
`multiply`, `divide`) using a dropdown menu. [`enum.Enum`][enum.Enum] offers a convenient
way to restrict values to a strict set of options, while providing `name: value`
pairs for each of the options. Here, the value for each choice is the actual
function we would like to have called when that option is selected.

```python
class Operation(enum.Enum):
    add = numpy.add
    subtract = numpy.subtract
    multiply = numpy.multiply
    divide = numpy.divide
```

### add it to napari

When we decorated the `image_arithmetic` function above, it became a
[FunctionGui][magicgui.widgets.FunctionGui].  Napari recognizes this type, so we
can simply add it to the napari viewer as follows:

```python
viewer.window.add_dock_widget(image_arithmetic)
```

### connect event listeners for interactivity

What fun is a GUI without some interactivity?  Let's make stuff happen.

We connect the `image_arithmetic.reset_choices` function to the
`viewer.layers.events.inserted/removed` event from `napari`, to make sure that
the dropdown menus stay in sync if a layer gets added or removed from the napari
window:

```python
viewer.layers.events.inserted.connect(image_arithmetic.reset_choices)
viewer.layers.events.removed.connect(image_arithmetic.reset_choices)
```

!!!tip
    An additional offering from `magicgui` here is that the decorated
    function also acquires a new attribute "`called`" that can be connected to
    callback functions of your choice.  Then, whenever the gui widget *or the
    original function* are called, the result will be passed to your callback
    function:

```python
@image_arithmetic.called.connect
def print_mean(value):
    # Callback function that accepts an event
    # the value attribute has the result of calling the function
    print(np.mean(value))
```

```
>>> image_arithmetic()
1.0060037881040373
```

## Code

Here's the full code example again.

"""

# %%
from enum import Enum

import napari
import numpy
from napari.types import ImageData

from magicgui import magicgui


class Operation(Enum):
    # A set of valid arithmetic operations for image_arithmetic.
    #
    # To create nice dropdown menus with magicgui, it's best
    # (but not required) to use Enums.  Here we make an Enum
    # class for all of the image math operations we want to
    # allow.
    add = numpy.add
    subtract = numpy.subtract
    multiply = numpy.multiply
    divide = numpy.divide


# here's the magicgui!  We also use the additional
# `call_button` option
@magicgui(call_button="execute")
def image_arithmetic(
    layerA: ImageData, operation: Operation, layerB: ImageData
) -> ImageData:
    # Add, subtracts, multiplies, or divides to image layers.
    return operation.value(layerA, layerB)


# create a viewer and add a couple image layers
viewer = napari.Viewer()
viewer.add_image(numpy.random.rand(20, 20), name="Layer 1")
viewer.add_image(numpy.random.rand(20, 20), name="Layer 2")

# add our new magicgui widget to the viewer
viewer.window.add_dock_widget(image_arithmetic)

# keep the dropdown menus in the gui in sync with the layer model
viewer.layers.events.inserted.connect(image_arithmetic.reset_choices)
viewer.layers.events.removed.connect(image_arithmetic.reset_choices)

napari.run()
