# napari image arithmetic widget

[napari](https://github.com/napari/napari) is a fast, interactive, multi-dimensional
image viewer for python.  It uses Qt for the GUI, so it's easy to extend napari with
small, composable widgets created with `magicgui`.  Here we're going to build this simple
image arithmetic widget with a few additional lines of code.

<p align="center"><img src="../../img/imagemath.gif" width="80%" /></p>

## outline

**This example demonstrates how to:**

[⬇️](#the-magic-part) Create a `magicgui` widget that can be used in another program (napari)

[⬇️](#create-dropdowns-with-enums) Use an `Enum` to create a dropdown menu

[⬇️](#register-a-custom-type) Tell `magicgui` how to handle a custom type annotation with `register_type()`

[⬇️](#connect-event-listeners-for-interactivity) Connect some event listeners to create interactivity.

## code

*Code follows, with explanation below... You can also [get this example at github](https://github.com/napari/magicgui/blob/master/examples/napari_image_arithmetic.py).*

???+ example "complete code"

    ```python hl_lines="17 18 19 20 31 32 33 34 45 46 47"
    import enum
    import numpy
    import napari
    from napari.layers import Layer, Image
    from magicgui import magicgui, register_type


    # Enums are a convenient way to get a dropdown menu
    class Operation(enum.Enum):
        add = numpy.add
        subtract = numpy.subtract
        multiply = numpy.multiply
        divide = numpy.divide


    # here we let magicgui know how to handle one of our custom types (layers.Layer)
    def get_layers(layer_type):
        return tuple(l for l in viewer.layers if isinstance(l, layer_type))

    register_type(Layer, choices=get_layers)


    with napari.gui_qt():  # the napari GUI requires a qt event loop...

        # create a new viewer with a couple image layers
        viewer = napari.Viewer()
        viewer.add_image(numpy.random.rand(20, 20), name=f"Layer 1")
        viewer.add_image(numpy.random.rand(20, 20), name=f"Layer 2")

        # here's the magicgui!  We also use the additional `call_button` option
        @magicgui(call_button="execute")
        def image_arithmetic(layerA: Image, operation: Operation, layerB: Image):
            """Adds, subtracts, multiplies, or divides two image layers of similar shape."""
            return operation.value(layerA.data, layerB.data)

        def show_result(result):
            """callback function for whenever the image_arithmetic functions is called"""
            try:
                viewer.layers["result"].data = result
            except KeyError:
                viewer.add_image(data=result, name="result")

        # instantiate the widget
        gui = image_arithmetic.Gui()
        # when the decorated function is called, send the result to our callback function
        image_arithmetic.called.connect(show_result)
        # add our new widget to the napari viewer
        viewer.window.add_dock_widget(gui)

        # connect some napari events to make sure that the dropdowns stay up-to-date
        viewer.layers.events.added.connect(lambda x: gui.fetch_choices("layerA"))
        viewer.layers.events.added.connect(lambda x: gui.fetch_choices("layerB"))
        viewer.layers.events.removed.connect(lambda x: gui.fetch_choices("layerA"))
        viewer.layers.events.removed.connect(lambda x: gui.fetch_choices("layerB"))

    ```

## walkthrough

We're going to go a little out of order so that the other code makes more sense.  Let's
start with the actual function we'd like to write to do some image arithmetic.

### the function

Our function takes two `napari` [Image
layers](https://napari.org/tutorials/fundamentals/image), and some mathematical operation
(we'll restrict the options using an `Enum`).  When called, our function calls the
selected operation on the two layers (which each have a `data` attribute that stores the
array info).

```python
def image_arithmetic(layerA: Image, operation: Operation, layerB: Image):
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
    While [type hints](https://docs.python.org/3/library/typing.html) aren't always
    required in `magicgui`, they are recommended (see [type
    inference](../../type_inference/#type-inference) )... and they *are* required for
    certain things, like the `Operation(Enum)` [used here for the
    dropdown](#create-dropdowns-with-enums) and the `napari.image.Image` annotations that
    we have previously registered with `magicgui`.

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

### register a custom type

`magicgui` knows how to handle most builtin types, but if provide an argument with a
custom class for a type annotation, you will need to tell `magicgui` how to handle it.
One way to do this is with a [`widget_type`](../../configuration/#widget_type)
argument-specific-option when calling `magicgui`.  However, you can do this globally for
a specific type by using [`register_type`](../../type_inference/#register_type) as shown in
this example, where we associate all annotations of type `napari.layers.Layer` with a
callback function that gets all layers of a specific type from the viewer instance.

```python
def get_layers(layer_type):
    return tuple(l for l in viewer.layers if isinstance(l, layer_type))
register_type(Layer, choices=get_layers)
```

see [`register_type`](../../type_inference/#register_type) for usage details.

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

The main offering from `magicgui` here is that the decorated function
(`image_arithmetic`) also acquires a new attribute/signal "`called`" that can be
connected to callback functions of your choice.  Then, whenever the gui widget *or the*
*original function* are called, the result will be passed to your callback function:

```python
def show_result(result):
    """callback function that takes the image math result and shows it in the viewer"""
    try:  # look for an existing layer called 'result'
        outlayer = viewer.layers["result"]
        outlayer.data = result
    except KeyError:  # or create one if it doesn't exist
        outlayer = viewer.add_image(data=result, name="result")

image_arithmetic.called.connect(show_result)
```
