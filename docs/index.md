# magicgui 🧙

[![License](https://img.shields.io/pypi/l/magicgui.svg)](LICENSE)
[![Version](https://img.shields.io/pypi/v/magicgui.svg)](https://pypi.python.org/pypi/magicgui)
[![Python Version](https://img.shields.io/pypi/pyversions/magicgui.svg)](https://python.org)

build functional GUIs with 2-way binding from functions, using magic.

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

# decorate your function with the ``@magicgui`` decorator
@magicgui(call_button="calculate")
def snells_law(aoi=30.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
    aoi = math.radians(aoi) if degrees else aoi
    try:
        result = math.asin(n1.value * math.sin(aoi) / n2.value)
        return math.degrees(result) if degrees else result
    except ValueError:
        # beyond the critical angle
        return "Total internal reflection!"

# your function will have a new attribute "Gui"
# calling it instantiates the widget (and, optionally, shows it)
snell_gui = snells_law.Gui(show=True)
```

## et voilà

[<img src="img/snells.png" width="542"/>](img/snells.png)

## two-way data binding

The fun is just beginning!  The new `snell_gui` object has attributes named after each of
the function parameters.  As you make changes in your new GUI, these attributes of the
`snell_gui` will be kept in sync.  For instance, change the first dropdown menu from
"Glass" to "Oil", and the corresponding parameter changes on `snell_gui`:

```python
In [2]: snell_gui.n1
Out[2]: <Medium.Oil: 1.515>
```

it goes both ways: change a parameter in the console and it will change in the GUI:

```python
In [3]: snell_gui.aoi = 47

In [4]: print(snell_gui)
<MagicGui: snells_law(aoi=47.0, n1=Medium.Glass, n2=Medium.Water, degrees=True)>
```

## calling the function

We can call our function in a few ways:

1. Because we provided the `call_button` argument to the `magicgui` decorator, a new
   button was created that will execute the function with the current gui parameters
   when clicked.  (*at the moment, we haven't hooked anything up to it, so it won't*
   *be all that interesting!*)

2. We can also directly call the original function. Now however, the current values from
   the GUI will be used as the default values for any arguments that are not explicitly
   provided to the function:

    ```python
    In [5]: snells_law()
    Out[5]: 56.22

    # Note: calling the gui object has the same result
    # as calling the original function:
    In [6]: snell_gui()
    Out[6]: 56.22
    ```

3. You can still override positional or keyword argumnets in the original function, just
   as you would with a regular function.  (Note: calling the function with values that
   differ from the GUI will *not* set the values in the GUI... It's just a one-time
   call).

    ```python
    # in radians, overriding the value for the second medium (n2)
    In [15]: snells_law(0.8, n2=Medium.Air, degrees=False)
    Out[15]: 'Total internal reflection!'
    ```

## connecting events

Usually in a GUI you are looking for something to happen as a result of calling the
function.  The original function (and the gui instance) will have a new `called` signal
that you can connect to an arbitrary callback function:

```python
def my_callback(result):
    # do something with the result, trigger other events, etc...
    ...

snells_law.called.connect(my_callback)
```

Now when you call `snells_law()`, or `snell_gui()` again, or click the `calculate` button
in the gui, `my_callback` will be called with the result of the calculation.

## @optional

Remember, `@decorators` are just [syntactic
sugar](https://en.wikipedia.org/wiki/Syntactic_sugar): you don't have to use `magicgui`
to decorate your function declaration. You can also just [call it with your function as
an argument](https://realpython.com/lessons/syntactic-sugar/):

```python
# the decorator in the first example could be replaced with this:
magic_snell = magicgui(snells_law, call_button='calculate')
snell_gui = magic_snell.Gui(show=True)
```

## configuration and advanced usage

The `@magicgui` decorator takes a number of options that allow you to configure the GUI
and it's behavior... More on that soon!