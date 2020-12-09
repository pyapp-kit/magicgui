# napari image arithmetic widget

[napari](https://github.com/napari/napari) is a fast, interactive,
multi-dimensional image viewer for python.  It uses Qt for the GUI, so it's easy
to extend napari with small, composable widgets created with `magicgui`.  Here
we're going to build this simple image arithmetic widget with a few additional
lines of code.

<p align="center"><img src="../../img/imagemath.gif" width="80%" /></p>

## outline

**This example demonstrates how to:**

[⬇️](#the-magic-part) Create a `magicgui` widget that can be used in another
program (napari)

[⬇️](#create-dropdowns-with-enums) Use an `Enum` to create a dropdown menu

[⬇️](#connect-event-listeners-for-interactivity) Connect some event listeners to
create interactivity.

## code

*Code follows, with explanation below... You can also [get this example at
github](https://github.com/napari/magicgui/blob/master/examples/napari_image_arithmetic.py).*

???+ example "complete code"

    ```python hl_lines="24 30 32 34"
    import enum
    import numpy
    import napari
    from napari.layers import Image
    from magicgui import magicgui


    # Enums are a convenient way to get a dropdown menu
    class Operation(enum.Enum):
        """A set of valid arithmetic operations for image_arithmetic."""
        add = numpy.add
        subtract = numpy.subtract
        multiply = numpy.multiply
        divide = numpy.divide


    with napari.gui_qt():
        # create a new viewer with a couple image layers
        viewer = napari.Viewer()
        viewer.add_image(numpy.random.rand(20, 20), name=f"Layer 1")
        viewer.add_image(numpy.random.rand(20, 20), name=f"Layer 2")

        # here's the magicgui!  We also use the additional `call_button` option
        @magicgui(call_button="execute")
        def image_arithmetic(layerA: Image, operation: Operation, layerB: Image) -> Image:
            """Adds, subtracts, multiplies, or divides two image layers of similar shape."""
            return operation.value(layerA.data, layerB.data)

        # instantiate the widget
        gui = image_arithmetic.Gui()
        # add our new widget to the napari viewer
        viewer.window.add_dock_widget(gui)
        # keep the dropdown menus in the gui in sync with the layer model
        viewer.layers.events.changed.connect(lambda x: gui.refresh_choices())
    ```

## walkthrough

We're going to go a little out of order so that the other code makes more sense.
Let's start with the actual function we'd like to write to do some image
arithmetic.

### the function

Our function takes two `napari` [Image
layers](https://napari.org/tutorials/fundamentals/image), and some mathematical
operation (we'll restrict the options using an `Enum`).  When called, our
function calls the selected operation on the two layers (which each have a
`data` attribute that stores the array info).

```python
def image_arithmetic(layerA, operation, layerB):
    return operation.value(layerA.data, layerB.data)
```

#### type annotations

`magicgui` works particularly well with [type
annotations](https://docs.python.org/3/library/typing.html), and allows
third-party libraries to register widgets for handling their custom types.
`napari` provides support for `magicgui` by registering a dropdown menu whenever
a function parameter is annotated as one of the basic napari [`Layer`
types](https://napari.org/tutorials/). Furthermore, it recognizes when a
function has a `Layer` return type annotation, and will add the result to the
viewer.  So we gain a *lot* by annotating the above function with the
appropriate `napari` types.

```python
def image_arithmetic(layerA: Image, operation: Operation, layerB: Image) -> Image:
    return operation.value(layerA.data, layerB.data)
```

### the magic part

 Finally, we decorate the function with `@magicgui` and tell it we'd like to have
a `call_button` that we can click to execute the function.

```python hl_lines="1"
@magicgui(call_button="execute")
def image_arithmetic(layerA: Image, operation: Operation, layerB: Image):
    return operation.value(layerA.data, layerB.data)
```

That's it!  The `image_arithmetic` function now has an attribute `image_arithmetic.Gui`
that we can call to instantiate our GUI.

```python
# instantiate the widget
gui = image_arithmetic.Gui()
```

!!! note
    While [type hints](https://docs.python.org/3/library/typing.html) aren't
    always required in `magicgui`, they are recommended (see [type
    inference](../../type_inference/#type-inference) )... and they *are*
    required for certain things, like the `Operation(Enum)` [used here for the
    dropdown](#create-dropdowns-with-enums) and the `napari.layers.Image`
    annotations that `napari` has registered with `magicgui`.

### create dropdowns with Enums

We'd like the user to be able to select the operation (`add`, `subtract`, `multiply`,
`divide`) using a dropdown menu.  `Enum`s offer a convenient way to restrict values to a
strict set of options, while providing `name: value` pairs for each of the options.
Here, the value for each choice is the actual function we would like to have called when
that option is selected.

```python
class Operation(enum.Enum):
    add = numpy.add
    subtract = numpy.subtract
    multiply = numpy.multiply
    divide = numpy.divide
```

### create the `magicgui` widget and add it to napari

When we decorated the `image_arithmetic` function above, it acquired a new attribute,
`Gui`, which when called, instantiates a new widget for your function. `Gui()` takes an
optional `show=True` argument, which was not used here, so the gui will not be shown
until it actually gets attached to the viewer.

```python
# instantiate the widget
gui = image_arithmetic.Gui()
# we use a napari method to add our new widget to the viewer
viewer.window.add_dock_widget(gui)
```

### connect event listeners for interactivity

What fun is a GUI without some interactivity?  Let's make stuff happen.

We connect the `gui.refresh_choices` function to the
`viewer.layers.events.changed` event from `napari`, to make sure that the
dropdown menus stay in sync if a layer gets added or removed from the napari
window:

```python
viewer.layers.events.changed.connect(lambda x: gui.refresh_choices())
```

An additional offering from `magicgui` here is that the decorated function
(`image_arithmetic`) also acquires a new attribute/signal "`called`" that can be
connected to callback functions of your choice.  Then, whenever the gui widget
*or the* *original function* are called, the result will be passed to your
callback function:

```python
def print_mean(result):
    """callback function that accepts the image math result"""
    print(result.mean())

image_arithmetic.called.connect(print_mean)
```
