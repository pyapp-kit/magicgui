# Type Hints to Widgets

## Annotation Mapping

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

## Using `typing.Annotated`

### Overriding the Default Widget

::: type_to_widget
    Annotated[int, {'widget_type': 'Slider'}]
    Annotated[float, {'widget_type': 'FloatSlider'}]

### Overriding the Default Kwargs

::: type_to_widget
    Annotated[int, {'step': 10, 'max': 50}]
    Annotated[int, {'choices': [1, 2, 3]}]

## Return Type Mapping

## Forward References

## Known Third-Party Support for magicgui

Any third-party library may use the [`magicgui.register_type`][] function to
register its types with magicgui.  When a registered type is used as an
annotation, the registered widget will be used.

!!! tip "Hi! :wave:"

     Have a library that registers types with magicgui?  [Let us know](https://github.com/pyapp-kit/magicgui/issues/new/choose) and we'll add it to this list!

### napari

[napari](https://napari.org) has registered a number of its types to provide
access to napari-specific objects using type annotations in magicgui. Details may be found in
napari's documentation on [using `magicgui` in
napari](https://napari.org/stable/guides/magicgui.html).