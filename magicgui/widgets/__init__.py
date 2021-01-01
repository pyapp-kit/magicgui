"""These are the main Widgets provided by magicgui.

While the primary API is to use the :func:`@magicgui <magicgui.magicgui>` decorator,
one can also instantiate widgets directly using any of these objects.

The :func:`create_widget` function is a helper function that will auto-pick and
instantiate the appropriate widget subclass given the arguments (type, annotation)
to the function.

"""

from functools import partial

from ._bases import Widget, create_widget
from ._concrete import (
    CheckBox,
    ComboBox,
    Container,
    DateTimeEdit,
    FileEdit,
    FloatSlider,
    FloatSpinBox,
    Label,
    LineEdit,
    LiteralEvalLineEdit,
    LogSlider,
    PushButton,
    RadioButton,
    RangeEdit,
    SliceEdit,
    Slider,
    SpinBox,
    TextEdit,
)

#: Aliases for compatibility with ipywidgets.  (WIP)
IntSlider = Slider
FloatLogSlider = LogSlider
IntText = SpinBox
BoundedIntText = SpinBox
FloatText = FloatSpinBox
BoundedFloatText = FloatSpinBox
ToggleButton = RadioButton
Checkbox = CheckBox
Dropdown = ComboBox
Text = LineEdit
Textarea = TextEdit
Combobox = ComboBox
DatePicker = DateTimeEdit
Box = Container
HBox = partial(Container, layout="horizontal")
VBox = partial(Container, layout="vertical")
Button = PushButton

__all__ = [
    "CheckBox",
    "ComboBox",
    "Container",
    "create_widget",
    "DateTimeEdit",
    "FileEdit",
    "FloatSlider",
    "FloatSpinBox",
    "Label",
    "LineEdit",
    "LiteralEvalLineEdit",
    "LogSlider",
    "PushButton",
    "RadioButton",
    "RangeEdit",
    "SliceEdit",
    "Slider",
    "SpinBox",
    "TextEdit",
    "Widget",
]

del partial
