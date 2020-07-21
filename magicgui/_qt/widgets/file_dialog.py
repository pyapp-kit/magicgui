"""Widgets that handle file dialogs."""
import os
from pathlib import Path
from typing import List, Tuple, Union

from qtpy.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget

from ..constants import FileDialogMode


class MagicFileDialog(QWidget):
    """A LineEdit widget with a QFileDialog button."""

    def __init__(
        self,
        *,
        parent=None,
        mode: Union[FileDialogMode, str] = FileDialogMode.EXISTING_FILE,
        filter: str = "",
    ):
        super().__init__(parent)
        self.line_edit = QLineEdit(self)
        self.choose_btn = QPushButton("Choose file", self)
        self.choose_btn.clicked.connect(self._on_choose_clicked)
        self.mode = mode
        self.filter: str = filter
        layout = QHBoxLayout(self)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.choose_btn)

    def _help_text(self):
        if self.mode is FileDialogMode.EXISTING_DIRECTORY:
            return "Choose directory"
        else:
            return "Select file" + ("s" if self.mode.name.endswith("S") else "")

    @property
    def mode(self):
        """Mode for the FileDialog."""
        return self._mode

    @mode.setter
    def mode(self, value: Union[FileDialogMode, str]):
        mode: Union[FileDialogMode, str] = value
        if isinstance(value, str):
            try:
                mode = FileDialogMode(value)
            except ValueError:
                try:
                    mode = FileDialogMode[value.upper()]
                except KeyError:
                    pass  # leave mode as string type, raises ValueError later
        # If mode is not a valid FileDialogMode enum type (eg: input string
        # could not be recognised and converted properly in the if block above)
        # then we raise a ValueError to alert the user.
        if not isinstance(mode, FileDialogMode):
            raise ValueError(
                f"{mode!r} is not a valid FileDialogMode. "
                f"Options include {set(i.name.lower() for i in FileDialogMode)}"
            )
        self._mode = mode
        self.choose_btn.setText(self._help_text())

    def _on_choose_clicked(self):
        show_dialog = getattr(QFileDialog, self.mode.value)
        start_path = self.get_path()
        if isinstance(start_path, tuple):
            start_path = start_path[0]
        start_path = os.fspath(os.path.abspath(os.path.expanduser(start_path)))
        caption = self._help_text()
        if self.mode is FileDialogMode.EXISTING_DIRECTORY:
            result = show_dialog(self, caption, start_path)
        else:
            result, _ = show_dialog(self, caption, start_path, self.filter)
        if result:
            self.set_path(result)

    def get_path(self) -> Union[Tuple[Path, ...], Path]:
        """Get current file path."""
        text = self.line_edit.text()
        if self.mode is FileDialogMode.EXISTING_FILES:
            return tuple(Path(p) for p in text.split(", "))
        return Path(text)

    def set_path(self, value: Union[List[str], Tuple[str, ...], str, Path]):
        """Set current file path."""
        if isinstance(value, (list, tuple)):
            value = ", ".join([os.fspath(p) for p in value])
        if not isinstance(value, (str, Path)):
            raise TypeError(
                f"value must be a string, or list/tuple of strings, got {type(value)}"
            )
        self.line_edit.setText(str(value))


class MagicFilesDialog(MagicFileDialog):
    """A LineEdit that forces multiple file selection with a QFileDialog button."""

    def __init__(self, **kwargs):
        kwargs["mode"] = "EXISTING_FILES"
        super().__init__(**kwargs)
