"""The main (instantiatable) widgets from magicgui.

While the primary API is to use the `@magicgui.magicgui` decorator, one can
also instantiate widgets directly using any of these objects.

The `create_widget()` function is a helper function that will instantiate and
return the appropriate widget subclass given the arguments (type, annotation)
to the function.
"""

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
