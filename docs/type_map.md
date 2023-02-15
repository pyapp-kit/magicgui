# Type Hints to Widgets

One of the key offerings of magicgui is the ability to automatically generate
Widgets from Python type hints.  This page describes how type hints are mapped
to Widgets, and how to customize that mapping.

## Annotation Mapping

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

## Customizing Widget Options with `typing.Annotated`

Widget options and types may be embedded in the type hint itself using
`typing.Annotated`.

!!! note

    This is not the *only* way to customize the widget type or options
    in magicgui.  Some functions (like [`magicgui.magicgui`][]) also accept
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

## Return Type Mapping

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

Any third-party library may use the [`magicgui.register_type`][] function to
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
