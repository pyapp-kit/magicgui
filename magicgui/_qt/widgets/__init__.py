"""Custom widgets for magicgui."""
from .file_dialog import MagicFileDialog, MagicFilesDialog
from .double_slider import QDoubleSlider
from .data_combobox import QDataComboBox
from .widget import WidgetType


__all__ = [
    "MagicFileDialog",
    "MagicFilesDialog",
    "QDoubleSlider",
    "QDataComboBox",
    "WidgetType",
]
