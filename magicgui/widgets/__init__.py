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
    DateEdit,
    DateTimeEdit,
    EmptyWidget,
    FileEdit,
    FloatSlider,
    FloatSpinBox,
    Label,
    LineEdit,
    LiteralEvalLineEdit,
    LogSlider,
    MainWindow,
    ProgressBar,
    PushButton,
    RadioButton,
    RadioButtons,
    RangeEdit,
    SliceEdit,
    Slider,
    SpinBox,
    TextEdit,
    TimeEdit,
)
from ._function_gui import FunctionGui, MainFunctionGui
from ._image import Image
from ._table import Table

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

__all__ = [
    "CheckBox",
    "ComboBox",
    "Container",
    "create_widget",
    "DateEdit",
    "DateTimeEdit",
    "EmptyWidget",
    "FileEdit",
    "FloatSlider",
    "FloatSpinBox",
    "FunctionGui",
    "Image",
    "Label",
    "LineEdit",
    "LiteralEvalLineEdit",
    "LogSlider",
    "MainFunctionGui",
    "MainWindow",
    "PushButton",
    "ProgressBar",
    "RadioButton",
    "RadioButtons",
    "RangeEdit",
    "SliceEdit",
    "Slider",
    "SpinBox",
    "Table",
    "TextEdit",
    "TimeEdit",
    "Widget",
]

del partial
