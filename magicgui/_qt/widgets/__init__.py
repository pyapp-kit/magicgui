"""Custom widgets for magicgui."""
from .data_combobox import QDataComboBox
from .double_slider import QDoubleSlider
from .eval_lineedit import LiteralEvalEdit
from .file_dialog import MagicFileDialog, MagicFilesDialog
from .log_slider import QLogSlider
from .widget import WidgetType

__all__ = [
    "LiteralEvalEdit",
    "MagicFileDialog",
    "MagicFilesDialog",
    "QDoubleSlider",
    "QLogSlider",
    "QDataComboBox",
    "WidgetType",
]
