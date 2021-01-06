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

# Types & Widgets

The central feature of `magicgui` is conversion from an argument type declared
in a function signature, to an appropriate widget type for the given backend.
This page describes the logic used.

```{eval-rst}
.. _type-inference:
```

## type inference

`magicgui` determines the `type` of an argument as follows:

1. If a [type hint](https://docs.python.org/3/library/typing.html) is provided, it is
   used (regardless of the `type` of the default value, if provided).
2. If no type hint is provided, the `type` of the default value is used, if one is
   provided.
3. If a bare argument is defined without a `type` annotation or default value, it is
   assumed to be a string.

```python
# arg is assumed to be a float
def function(arg: float = 1):
    ...

# arg is assumed to be a float
def function(arg = 1.0):
    ...

# arg is assumed to be a str
def function(arg):
    ...
```

## type-to-widget conversion

Using a set of {func}`~magicgui.type_map.type_matcher`s and other logic defined
in the {mod}`magicgui.type_map` module, magicgui will select an appropriate
{class}`~magicgui.widgets._bases.Widget` subclass to display the any given type
or type annotation. To see the default type of widget magicgui will for a given
value, use the {func}`~magicgui.type_map.get_widget_class` function:

```{code-cell} python
import datetime
from enum import Enum
from pathlib import Path
from magicgui.type_map import get_widget_class

Animal = Enum('Animal', 'ANT BEE CAT DOG')
values = [
    True, 1, 3.43, 'text', Path.home(),
    datetime.datetime.now(), datetime.time(12, 30),
    datetime.date(2000, 2, 18),
    Animal.ANT, range(10), slice(1,20), lambda x: x
]
for v in values:
    cls, options = get_widget_class(v)
    print(f"The widget for {type(v)} is {cls.__name__!r}")
```

## `register_type`

To provide custom behavior for a specific object type, you may use the
{func}`magicgui.type_map.register_type` function to:

1. register a special `widget_type`
2. register a special set of `choices` used when magicgui encounters that type
3. control what happens when magicgui encounters a function with a return
   annotation of your custom type.

```{hint}
This is how [napari](https://napari.org) registers itself to handle napari-specific
types in magicgui functions, as shown in [the examples](../examples/napari/napari_img_math.md)
```

## drop-down menus

to get a [drop-down list](https://en.wikipedia.org/wiki/Drop-down_list):

- use an {class}`~enum.Enum` as either the default value or type hint for an argument

```{code-cell} python
from magicgui import magicgui
from enum import Enum

class RefractiveIndex(Enum):
    Oil = 1.515
    Water = 1.33
    Air = 1.0

@magicgui
def function_a(ri = RefractiveIndex.Water):
    ...

function_a.show()
```

- provide a `choices` [parameter-specific
  option](configuration#parameter-specific-options) when calling `@magicgui`
  on a function that has a parameter named `arg`.

```{code-cell} python
@magicgui(ri={"choices": ["Oil", "Water", "Air"]})
def function_b(ri="Water"):
    ...

function_b.show()
```

````{note}
In the first example using an {class}`~enum.Enum`, the value of the attribute
will be an enum instance.  In the second example using a `choices` list, the
value will be a simple string:

```python
>>> print(repr(function_a.ri.value))
<RefractiveIndex.Water: 1.33>
>>> print(repr(function_b.ri.value))
'Water'
```

If you'd like to have a drop-down menu with strings labels, but don't want to
use an {class}`~enum.Enum`, you can use a list of 2-tuples:

```python
@magicgui(ri={"choices": [("Oil", 1.515), ("Water", 1.33), ("Air", 1.0)]})
def function_c(ri=1.33):
    ...
```

```python
>>> print(repr(function_c.ri.value))
1.33
```
````
