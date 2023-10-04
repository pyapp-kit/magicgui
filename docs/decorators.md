# magicgui & magic_factory

## From Object to GUI

The eponymous feature of `magicgui` is the [`magicgui.magicgui`][magicgui.magicgui] function,
which converts an object into a widget.

!!! info
    Currently, the only supported objects are functions, but in the future
    `magicgui.magicgui` may accept other objects, such as
    [dataclass instances](./dataclasses.md)

When used to decorate a function, `@magicgui` will autogenerate a graphical user
interface (GUI) by inspecting the function signature and adding an appropriate
GUI widget for each parameter, as described in [Type Hints to
Widgets](./type_map.md). Parameter `types` are taken from [type
hints](https://docs.python.org/3/library/typing.html), if provided, or inferred
using the type of the default value otherwise.

```python
import math
from enum import Enum
from magicgui import magicgui

# dropdown boxes are best made by creating an enum
class Medium(Enum):
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003

# decorate your function with the @magicgui decorator
@magicgui(call_button="calculate")
def snells_law(aoi=30.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
    aoi = math.radians(aoi) if degrees else aoi
    try:
        result = math.asin(n1.value * math.sin(aoi) / n2.value)
        return math.degrees(result) if degrees else result
    except ValueError:
        # beyond the critical angle
        return "Total internal reflection!"

snells_law.show() # leave open
```

The object returned by the `magicgui` decorator is an instance of [`magicgui.widgets.FunctionGui`][magicgui.widgets.FunctionGui].  It can still be called like the original function, but it also knows how to present itself as a GUI.

## Two-Way Data Binding

The modified `snells_law` object gains attributes named after each of the
parameters in the function.  Each attribute is an instance of a
[`magicgui.widgets.Widget`][magicgui.widgets.Widget] subclass (suitable for the data type represented by
that parameter). As you make changes in your GUI, the attributes of the
`snells_law` object will be kept in sync.  For instance, change the first
dropdown menu from "Glass" to "Oil", and the corresponding `n1` object on
`snells_law` will change its value to `1.515`:

```python
snells_law.n1.value  # 1.515
```

It goes both ways: set a parameter in the console and it will change in the GUI:

```python
snells_law.aoi.value = 47
snells_law.show()
```

## It's still a function

`magicgui` tries very hard to make it so that the decorated object behaves as
much like the original object as possible.

We can invoke the function in a few ways:

* Because we provided the `call_button` argument to the
  [`magicgui`][magicgui.magicgui] decorator, a new button was created that will
  execute the function with the current gui parameters when clicked.

* We can call the object just like the original function.

    ```python
    snells_law()        # 34.7602
    snells_law(aoi=12)  # 13.7142
    ```

    Now however, the current values from the GUI will be used as the default
    values for any arguments that are not explicitly provided to the function.

    ```python
    snells_law.aoi.value = 12
    snells_law()  # 13.7142
    snells_law(aoi=30)  # 34.7602
    ```

    In essence, your original function now has a "living" signature whose
    defaults change as the user interacts with your GUI.

    ```python
    import inspect

    inspect.signature(snells_law)
    # <MagicSignature(
    #   aoi=12.0, n1=<Medium.Glass: 1.52>, n2=<Medium.Water: 1.333>, degrees=True
    # )>
    # notice how the default `aoi` is now 12 ... because we changed it above
    ```

* You can still override positional or keyword arguments in the original
  function, just as you would with a regular function.

    !!! note
        calling the function with values that differ from the GUI will *not* set
        the values in the GUI... It's just a one-time call.

    ```python
    # in radians, overriding the value for the second medium (n2)
    snells_law(0.8, n2=Medium.Air, degrees=False)  # 'Total internal reflection!'
    ```

## Connecting Events

### Function Calls

With a GUI, you are usually looking for something to happen as a result of
calling the function.  The function will have a new `called` attribute that you
can `connect` to an arbitrary callback function:

```python
@snells_law.called.connect
def my_callback(value: str):
    # The callback receives an `Event` object that has the result
    # of the function call in the `value` attribute
    print(f"Your function was called! The result is: {value}")

result = snells_law()
```

Now when you call `snells_law()`, or click the `calculate` button in the gui,
`my_callback` will be called with the result of the calculation.

### Parameter Changes

You can also listen for changes on individual function parameters by connecting
to the `<parameter_name>.changed` signal:

```python
# whenever the current value for n1 changes, print it to the console:
@snells_law.n1.changed.connect
def _on_n1_changed(x: Medium):
    print(f"n1 was changed to {x}")

snells_law.n1.value = Medium.Air
```

!!! note
    This signal will be emitted regardless of whether the parameter was changed in
    the GUI or via by [directly setting the paramaeter on the gui
    instance](#two-way-data-binding).

## Usage As a Decorator is Optional

Remember: the `@decorator` syntax is just [syntactic
sugar](https://en.wikipedia.org/wiki/Syntactic_sugar).  You don't *have* to use
`@magicgui` to decorate your function declaration. You can also just [call it
with your function as an
argument](https://realpython.com/lessons/syntactic-sugar/):

This decorator usage:

```python
@magicgui(auto_call=True)
def function():
    pass
```

is equivalent to this:

```python
def function():
    pass

function = magicgui(function, auto_call=True)
```

In many cases, it will actually be desirable *not* to use magicgui as a
decorator if you don't need a widget immediately, but want to create one later
(see also the [`magic_factory`](#magic_factory) decorator.)

```python
# some time later...
widget_instance = magicgui(function)
```

## magic_factory

The [`magicgui.magic_factory`][magicgui.magic_factory] function/decorator acts very much like the `magicgui`
decorator, with one important difference:

**Unlike `magicgui`, `magic_factory` does not return a widget instance
immediately.  Instead, it returns a "factory function" that can be *called*
to create a widget instance.**

This is an important distinction to understand.  In most cases, the `@magicgui`
decorator is useful for interactive use or rapid prototyping.  But if you are
writing a library or package where someone *else* will be instantiating your
widget (a napari plugin is a good example), you will likely want to use
`magic_factory` instead, (or create your own [Widget Container](widgets.md#containerwidget)
subclass).

!!! tip "it's just a partial"

    If you're familiar with [`functools.partial`][functools.partial], you can think of
    `magic_factory` as a partial function application of the `magicgui`
    decorator (in fact, `magic_factory` is a subclass of `partial`).
    It is very roughly equivalent to:

    ```python
    def magic_factory(func, *args, **kwargs):
        return partial(magicgui, func, *args, **kwargs)
    ```

### `widget_init`

`magic_factory` gains one additional parameter: `widget_init`.  This accepts
a callable that will be called with the new widget instance each time the
factory is called.  This is a convenient place to add additional initialization
or connect [events](events.md).

```python
from magicgui import magic_factory

def _on_init(widget):
    print("widget created!", widget)
    widget.y.changed.connect(lambda x: print("y changed!", x))

@magic_factory(widget_init=_on_init)
def my_factory(x: int, y: str): ...

new_widget = my_factory()
```



## The (lack of) "magic" in magicgui

Just to demystify the name a bit, there really isn't a whole lot of "magic"
in the `magicgui` decorator.  It's really just a thin wrapper around the
[`magicgui.widgets.create_widget`][magicgui.widgets.create_widget] function, to create a
[`Container`][magicgui.widgets.Container] with a sub-widget for each
parameter in the function signature.

The widget creation is very roughly equivalent to something like this:

```python
from inspect import signature, Parameter
from magicgui.widgets import create_widget, Container
from magicgui.types import Undefined


def pseudo_magicgui(func: 'Callable'):
    return Container(
        widgets=[
            create_widget(p.default, annotation=p.annotation, name=p.name)
            for p in signature(func).parameters.values()
        ]
    )

def some_func(x: int = 2, y: str = 'hello'):
    return x, y

my_widget = pseudo_magicgui(some_func)
my_widget.show()
```

In the case of `magicgui`, a special subclass of `Container`
([`FunctionGui`][magicgui.widgets.FunctionGui]) is used, which additionally adds
a `__call__` method that allows the widget to [behave like the original
function](#its-still-a-function).
