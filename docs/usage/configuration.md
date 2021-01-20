---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.12
    jupytext_version: 1.7.1
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Configuration

If used without arguments, the {func}`~magicgui.magicgui` decorator will build
you a GUI using the default settings, making some reasonable default guesses
about [what type of GUI widget to use](types_widgets), based on the type or
type annotation of your argument:

```{code-cell} python
import enum
import pathlib

from datetime import datetime
from magicgui import magicgui

class Choice(enum.Enum):
    A = 'Choice A'
    B = 'Choice B'
    C = 'Choice C'

@magicgui
def widget_demo(
    boolean=True,
    number=1,
    string="Text goes here",
    dropdown=Choice.A,
    filename=pathlib.Path.home(),
):
    """Run some computation."""
    ...

widget_demo.show()
```

However, {func}`~magicgui.magicgui` also accepts a number of options to
configure your GUI:

## `magicgui` options

### `call_button`

If a `call_button` argument is provided that evaluates to `True`, a button will
be added to the gui which, when clicked, will call the decorated function with
the current values from the gui.  If a `str` is provided to `call_button`, it
will be used as the text of the button.

```{code-cell} python
@magicgui(call_button='Add')
def add(a: int, b: int) -> int:
    return a + b

add.show()
```

### `auto_call`

Whereas `call_button` provides a button for the user to manually trigger
execution of the function, using `auto_call=True` will automatically call
the underlying function with the updated arguments each time the user
changes a value in the gui (or when the value is changed via the console)

```{code-cell} python
@magicgui(auto_call=True)
def add(a: int, b: int = 15) -> int:
    result = a + b
    print(f"{a} + {b} = {result}")
    return result

add.a.value = 4
add.show()
```

### `layout`

The `layout` option determines the layout of the layout.
Currently, only `horizontal`, `vertical` are supported. Grid Layouts are a work
in progress...

```{code-cell} python
@magicgui(layout='vertical', call_button='Add')
def add(a: int, b: int) -> int:
    return a + b

add.show()
```

```{eval-rst}
.. _parameter-specific-options:
```

## parameter-specific options

As a reminder, a widget will be created in the GUI for each parameter in the
signature of the function being decorated by `magicgui`.  These individual widgets
can also be modified by providing an `dict` of options to a keyword argument in
the call to `magicgui` with the same name as the parameter in the signature that
you want to modify:

```{code-cell} python
@magicgui(b={'min': 10, 'max': 20})
def add(a: int, b: int = 15) -> int:
    return a + b

add.show()
```

```{caution}
The keys in the parameter-specific options dict must be valid arguments
for the corresponding widget type from {mod}`magicgui.widgets`.  In this
example, the `a_string` paremeter would be turned into a
{class}`~magicgui.widgets.LineEdit` widget, which does not take an
argument "`min`":
```

```{code-cell} python
---
tags: [warns]
---
@magicgui(a_string={'min': 10})
def whoops(a_string: str = 'Hi there'):
    ...
```

### `widget_type`

You can override the type of widget used for a given parameter using the
`widget_type` parameter-specific option.  It can be a string name of any
widget in [magicgui.widgets](magicgui.widgets).  Or an actual
{class}`magicgui.widgets.Widget` subclass.  For instance, to turn an
`int` into a slider:

```{code-cell} python
@magicgui(b={'widget_type': 'Slider', 'min': 10, 'max': 20})
def add(a: int, b: int = 15) -> int:
    return a + b

add.show()
```

### `label`

By default, the label which will be displayed next to the widget will have the
variable's name. If you wish to modify that, add a `label` entry to the
parameter-specific options dictionary with the desired label:

```{code-cell} python
@magicgui(user_address={'label': 'Enter Address:'})
def get_address(user_address: str):
    ...

get_address.show()
```

## `labels`

Labels are shown by default, but can be hidden by using the `labels` argument
to the `@magicgui` decorator.

```{code-cell} python
@magicgui(labels=False)
def hidden_labels(x = 1, y = 'hello'):
    ...

hidden_labels.show()
```

## `result_widget`

If you'd like to just show the result of calling the function directly
in the gui, you can use the `result_widget=True` option:

```{code-cell} python

@magicgui(result_widget=True, labels=False, auto_call=True)
def add(a=2, b=3):
    return a + b

add()
add.show()
```

```{tip}
The object returned from {func}`magicgui.magicgui` is a
{class}`~magicgui.widgets.FunctionGui`, which is in turn just
a special type of {class}`~magicgui.widgets.Container` widget. A `Container`
acts just like a basic python list.  So in the example above, we could
manually add a {class}`~magicgui.widgets.Label` with "`+`" to our widget as
follows:
```

```{code-cell} python
from magicgui.widgets import Label

@magicgui(result_widget=True, labels=False, auto_call=True)
def add(a=2, b=3):
    return a + b

add.insert(1, Label(value="+"))
add.insert(3, Label(value="="))
add()
add.show()
```

Currently, the result widget is always a {class}`~magicgui.widgets.LineEdit`
widget, but future development will allow the return annotation of the function
to dictate what type of widget is used to show the result.  For instance, a
[`pandas.Dataframe`](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html)
(or a `List[dict]`) might render a Table Widget.
