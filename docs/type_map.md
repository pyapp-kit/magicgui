# Type Hints to Widgets

One of the key offerings of magicgui is the ability to automatically generate
Widgets from Python type hints.  This page describes how type hints are mapped
to Widgets, and how to customize that mapping.

## Default Type Mapping

By default, The following python `Type Hint` annotations are mapped to the
corresponding `Widget` class, and parametrized with the corresponding `kwargs`
(when applicable):

::: type_to_widget
    bool
    int
    float
    str
    range
    slice
    list
    tuple
    pathlib.Path
    os.PathLike
    Sequence[pathlib.Path]
    datetime.time
    datetime.timedelta
    datetime.date
    datetime.datetime
    Literal['a', 'b']
    Set[Literal['a', 'b']]
    enum.Enum
    magicgui.widgets.ProgressBar
    types.FunctionType
    pint.Quantity

### Example

```python
from magicgui import widgets
import pathlib
import os
import datetime
from typing import Literal, Set, Sequence
import types
import pint
import enum

types = [
    bool, int, float, str, range, slice, list,
    pathlib.Path, os.PathLike, Sequence[pathlib.Path],
    datetime.time, datetime.timedelta, datetime.date, datetime.datetime,
    Literal['a', 'b'], Set[Literal['a', 'b']], enum.Enum,
    widgets.ProgressBar, pint.Quantity,
]

wdg = widgets.Container(
    widgets=[
        widgets.create_widget(annotation=t, label=str(t)) for t in types
    ]
)
wdg.show()
```

## Customizing Widget Options with `typing.Annotated`

Widget options and types may be embedded in the type hint itself using
[`typing.Annotated`][typing.Annotated].


!!! note
    This is not the *only* way to customize the widget type or options
    in magicgui.  Some functions (like [`magicgui.magicgui`][magicgui.magicgui]) also accept
    `**param_options` keyword arguments that map parameter names to
    dictionaries of widget options.


### Overriding the Default Type

To override the widget class used for a given object type, use the `widget_type`
key in the `Annotated` `kwargs`.  It can be either the string name of one of the
[built-in widgets](./api/widgets/index.md), or any
[`Widget`][magicgui.widgets.Widget] subclass object.

::: type_to_widget
    Annotated[int, {'widget_type': 'Slider'}]
    Annotated[float, {'widget_type': 'FloatSlider'}]

### Overriding the Default Options

Any additional kwargs will be passed to the widget constructor (and must be
valid for the corresponding widget type).

::: type_to_widget
    Annotated[int, {'step': 10, 'max': 50}]
    Annotated[int, {'choices': [1, 2, 3]}]

### Examples

Create a widget using standard type map:

=== "create_widget"

    ```python
    my_widget = widgets.create_widget(value=42, annotation=int)
    ```

=== "magicgui decorator"

    ```python
    from magicgui import magicgui

    @magicgui
    def my_widget(x: int = 42):
        return x
    ```

=== "guiclass decorator"

    ```python
    from magicgui.experimental import guiclass

    @guiclass
    class MyObject:
        x: int = 42

    obj = MyObject()
    my_widget = obj.gui
    ```

Customize a widget using [`typing.Annotated`][typing.Annotated]:

=== "create_widget"

    ```python
    from typing import Annotated

    Int10_50 = Annotated[int, (('widget_type', 'Slider'),('step', 10),('max', 50))]
    wdg2 = widgets.create_widget(value=42, annotation=Int10_50)
    ```

=== "magicgui decorator"

    ```python
    from magicgui import magicgui
    from typing import Annotated

    Int10_50 = Annotated[int, (('widget_type', 'Slider'),('step', 10),('max', 50))]

    @magicgui
    def my_widget(x: Int10_50 = 42):
        ...
    ```

=== "guiclass decorator"

    ```python
    from magicgui.experimental import guiclass
    from typing import Annotated

    Int10_50 = Annotated[int, (('widget_type', 'Slider'),('step', 10),('max', 50))]

    @guiclass
    class MyObject:
        x: Int10_50 = 42

    obj = MyObject()
    my_widget = obj.gui
    ```

Note that you may also customize widget creation with kwargs to
[`create_widget`][magicgui.widgets.create_widget]

```python
from typing import Annotated
from magicgui.widgets import Slider

options = {'step': 10, 'max': 50}
wdg3 = widgets.create_widget(value=42, widget_type=Slider, options=options)
wdg3.show()
```

... or to the [`magicgui`][magicgui.magicgui] decorator:

```python
@magicgui(x={'widget_type': 'Slider', 'step': 10, 'max': 50})
def my_widget(x: int = 42):
    ...

my_widget.show()
```

## Return Type Mapping

In some cases, magicgui may be able to create a widget for the *return*
annotation of a function.

... more to come ...

## Postponed annotations

Using forward references and `__future__.annotations` with magicgui
is possible, but requires some extra care.  Read on for more details.

### Forward References

When a type hint contains names that have not been defined yet, that definition
may be expressed as a string literal, to be resolved later.  This is called a
`Forward Reference` ([see PEP 484](https://peps.python.org/pep-0484/#forward-references)).  This is useful when you want to use a type hint that refers to a type that has not yet been defined, or when you want to avoid importing a type that is only used in a type hint.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mymodule import MyType

def my_function(x: 'MyType') -> None:
    ...
```

### :warning: `__future__.annotations`

In Python 3.7, the `__future__.annotations` feature was introduced ([PEP
563](https://peps.python.org/pep-0563/)), which postpones the evaluation of
type annotations.  The effect of this is that *no* type annotations will be
evaluated at definition time, and all type annotations will be treated as
strings (regardless of whether they are enclosed in quotes or not).

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mymodule import MyType

# no longer necessary to use quotes around 'MyType'
def my_function(x: MyType) -> None:
    ...
```

While this is a useful feature for developers, it does make it significantly
more difficult to *use* those type annotations at runtime.

Magicgui does attempt to resolve forward references it encounters (see [Resolving type hints at runtime](https://peps.python.org/pep-0563/#resolving-type-hints-at-runtime) for gory details), but this is an imperfect process, and may not always work.

### If You Must Use Postponed Annotations

As a general rule, if you *must* use forward references or
`__future__.annotations` in a module that uses magicgui, you should:

- don't use typing syntax that is not valid for ALL python versions
  you wish to support (e.g. `str | int` instead of `Union[str, int]`
  in python < 3.10), as these will raise an exception when magicgui
  attempts to evaluate them at runtime.
- use fully qualified names for all type hints, as these will be
  easier for magicgui to resolve without user-supplied namespaces.

    ```python
    from __future__ import annotations

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        import mymodule

    # this is easier for magicgui to resolve
    def my_function(x: mymodule.MyType) -> None:
        ...
    ```

## Registering Support for Custom Types

Any third-party library may use the [`magicgui.register_type`][magicgui.register_type] function to
register its types with magicgui.  When a registered type is used as an
annotation, the registered widget will be used.

### Known Third-Party Support for magicgui

!!! tip "Hi developer! :wave:"

     Have a library that registers types with magicgui?  [Let us know](https://github.com/pyapp-kit/magicgui/issues/new/choose) and we'll add it to this list!

#### napari

[napari](https://napari.org) has registered a number of its types to provide
access to napari-specific objects using type annotations in magicgui. Details may be found in
napari's documentation on [using `magicgui` in
napari](https://napari.org/stable/guides/magicgui.html).
