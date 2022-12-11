# Mapping Types to Widgets

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
