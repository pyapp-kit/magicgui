# types & widgets

!!! warning "API in flux!"
    This documentation is being written while the project is still in heavy development.
    API is subject to change.

The central feature of `magicgui` is conversion from an argument type declared in a
function signature, to an appropriate widget type for the given backend.  This page
describes the logic used.

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

## drop-down menus

to get a [drop-down list](https://en.wikipedia.org/wiki/Drop-down_list):

- use an `Enum` as either the default value or type hint for an argument

```python
class RefractiveIndex(Enum):
    Oil = 1.515
    Water = 1.33
    Air = 1.0

def function(ri = RefractiveIndex.Water):
    ...
```

- use `arg['choices']` when calling `@magicgui`.

```python
@magicgui(arg={"choices": ["Oil", "Water", "Air"]})
def function(ri="Water"):
    ...
```

## `register_type`

The `magicgui.register_type` function takes a required argument (a `type`) and *either*
the desired corresponding `widget_type` (a widget class in the chosen backend, such as
`QWidget`, or `QSlider` for Qt), *OR* the `choices` argument, which will not only set
the `widget_type` to the default categorical widget (e.g. a `QComboBox` for Qt), but will
also set the available choices as provided.  `choices` must be either an `Enum` subclass,
a sequence (usually of `str`), or a callable function.  If a callable is provided, it
must take a single argument: the `type` of the argument in the signature.

```python
ChoicesType = Union[EnumMeta, Iterable, Callable[[Type], Iterable]]

def register_type(
    type_: type,
    *,
    widget_type: Optional[Type[api.WidgetType]] = None,
    choices: Optional[ChoicesType] = None,
) -> None:
    if widget_type is None and choices is None:
        raise ValueError("either `widget_type` or `choices` must be provided.")
    ...
```

???+ example

    Take the package [`napari`](https://github.com/napari/napari) for example:
    it defines a custom `Layer` class that has a bunch of subclasses (`Image`, `Surface`, etc...).  We can tell `magicgui` what do to whenever it sees `napari.Layer` or one of
    its subclasses in a function signature type annotation:

    ```python
    from napari.layers import Layer, Image

    def get_current_layers():
        """some function to get current layers from the viewer"""
        ...

    def get_layer_choices(arg_type):
        """callback that returns all layers of a specific type"""
        return tuple(l for l in get_current_layers() if isinstance(l, arg_type))

    # all sublcasses of layers.Layer will also use this callback
    # to retrieve the current "layer choices".
    register_type(layers.Layer, choices=get_layer_choices)

    # ... then later
    # the `layer` argument here will be rendered as a dropdown populated *only*
    # by Image layers, (no other subclasses).
    @magicgui
    def myfunction(layer: layers.Image):
        ...
    ```

### for developers

If you have a Qt-driven GUI program that offers your users some custom classes, you can
provide support for your types for those who have installed `magicgui` in a `try/catch`:

```python
from . import MyCustomClass
from ._qt import MyCustomQtWidget

try:
    from magicgui import register_type

    register_type(MyCustomClass, widget_type=MyCustomQtWidget)
except ImportError:
    pass
```
