"""Constants for the _qt module."""
from enum import Enum, EnumMeta

from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QVBoxLayout,
    QWidget,
)


class HelpfulEnum(EnumMeta):
    """Metaclass that shows the available options on KeyError."""

    def __getitem__(self, name: str):
        """Get enum by name, or raise helpful KeyError."""
        try:
            return super().__getitem__(name)
        except (TypeError, KeyError):
            options = set(self.__members__.keys())
            raise KeyError(
                f"'{name}' is not a valid Layout. Options include: {options}"
            )


class FileDialogMode(Enum, metaclass=HelpfulEnum):
    """FileDialog mode options.

    EXISTING_FILE - returns one existing file.
    EXISTING_FILES - return one or more existing files.
    OPTIONAL_FILE - return one file name that does not have to exist.
    EXISTING_DIRECTORY - returns one existing directory.
    R - read mode, Alias of EXISTING_FILES.
    W - write mode, Alias of OPTIONAL_FILE.
    W - directory mode, Alias of OPTIONAL_FILE.
    """

    EXISTING_FILE = "getOpenFileName"
    EXISTING_FILES = "getOpenFileNames"
    OPTIONAL_FILE = "getSaveFileName"
    EXISTING_DIRECTORY = "getExistingDirectory"
    # Aliases
    R = "getOpenFileName"
    W = "getSaveFileName"
    D = "getExistingDirectory"


class Layout(Enum, metaclass=HelpfulEnum):
    """QLayout options."""

    vertical = QVBoxLayout
    horizontal = QHBoxLayout
    grid = QGridLayout
    form = QFormLayout

    @staticmethod
    def addWidget(layout: QLayout, widget: QWidget, label: str = ""):
        """Add widget to arbitrary layout with optional label."""
        if isinstance(layout, QFormLayout):
            return layout.addRow(label, widget)
        elif isinstance(layout, (QHBoxLayout, QVBoxLayout)):
            if label:
                label_widget = QLabel(label)
                label_widget.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
                layout.addWidget(label_widget)
            return layout.addWidget(widget)

    @staticmethod
    def insertWidget(layout: QLayout, position: int, widget: QWidget, label: str = ""):
        """Add widget to arbitrary layout at position, with optional label."""
        if position < 0:
            position = layout.count() + position + 1
        if isinstance(layout, QFormLayout):
            layout.insertRow(position, label, widget)
        else:
            layout.insertWidget(position, widget)
            if label:
                label_widget = QLabel(label)
                label_widget.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
                layout.insertWidget(position, label_widget)
