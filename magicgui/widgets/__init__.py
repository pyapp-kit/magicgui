"""These are the main Widgets provided by magicgui.

While the primary API is to use the :func:`magicgui.magicgui` decorator, one can
also instantiate widgets directly using any of these objects.

The :func:`create_widget` function is a helper function that will auto-pick and
instantiate the appropriate widget subclass given the arguments (type, annotation)
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
