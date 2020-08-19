"""Main Widget Types.

-> Widget
    ↪ ValueWidget
        - Label
        - LineEdit
        - TextEdit
        - DateTimeEdit

        ↪ ButtonWidget
            - PushButton
            - CheckBox
            - RadioButton

        ↪ RangedWidget
            - SpinBox
            - FloatSpinBox

            ↪ SliderWidget
                - Slider
                - FloatSlider

        ↪ CategoricalWidget
            - ComboBox

    ↪ Container
        - Container
"""
from __future__ import annotations

import inspect
import os
from pathlib import Path
from typing import Any, Sequence, Tuple, Union

from magicgui import widget_wrappers as ww
from magicgui.application import use_app
from magicgui.constants import FileDialogMode


class Label(ww.ValueWidget):
    pass


class LineEdit(ww.ValueWidget):
    def __init__(
        self,
        name: "str" = "",
        kind=None,
        default: "Any" = None,
        annotation: "Any" = None,
        gui_only=False,
    ):
        super()


class TextEdit(ww.ValueWidget):
    pass


class DateTimeEdit(ww.ValueWidget):
    pass


class PushButton(ww.ButtonWidget):
    pass


class CheckBox(ww.ButtonWidget):
    pass


class RadioButton(ww.ButtonWidget):
    pass


class SpinBox(ww.RangedWidget):
    pass


class Slider(ww.RangedWidget):
    pass


class ComboBox(ww.CategoricalWidget):
    pass


class Container(ww.Container):
    """Widget that can contain other widgets."""


PathLike = Union[Path, str, bytes]


class FileEdit(Container):
    """A LineEdit widget with a button that opens a FileDialog"""

    def __init__(
        self,
        *,
        name: str = "",
        kind: inspect._ParameterKind = inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default: Any = inspect.Parameter.empty,
        annotation=None,
        gui_only=False,
        orientation="horizontal",
        mode: FileDialogMode = FileDialogMode.EXISTING_FILE,
    ):
        self.line_edit = LineEdit()
        self.choose_btn = PushButton()
        self.mode = mode  # sets the button text too
        super().__init__(
            orientation=orientation,
            widgets=[self.line_edit, self.choose_btn],
            name=name,
            kind=kind,
            default=default,
            annotation=annotation,
            gui_only=gui_only,
            widget_type="Container",
        )
        self._show_file_dialog = use_app().get_obj("show_file_dialog")
        self.choose_btn.changed.connect(self._on_choose_clicked)

    @property
    def mode(self) -> FileDialogMode:
        """Mode for the FileDialog."""
        return self._mode

    @mode.setter
    def mode(self, value: Union[FileDialogMode, str]):
        self._mode = FileDialogMode(value)
        self.choose_btn.text = self._btn_text

    @property
    def _btn_text(self) -> str:
        if self.mode is FileDialogMode.EXISTING_DIRECTORY:
            return "Choose directory"
        else:
            return "Select file" + ("s" if self.mode.name.endswith("S") else "")

    def _on_choose_clicked(self, event=None):
        _p = self.value
        start_path: Path = _p[0] if isinstance(_p, tuple) else _p
        start_path = os.fspath(start_path.expanduser().absolute())
        result = self._show_file_dialog(
            self.mode, caption=self._btn_text, start_path=start_path
        )
        if result:
            self.value = result

    @property
    def value(self) -> Union[Tuple[Path, ...], Path]:
        """Return current value of the widget.  This may be interpreted by backends."""
        text = self.line_edit.value
        if self.mode is FileDialogMode.EXISTING_FILES:
            return tuple(Path(p) for p in text.split(", "))
        return Path(text)

    @value.setter
    def value(self, value: Union[Sequence[PathLike], PathLike]):
        """Set current file path."""
        if isinstance(value, (list, tuple)):
            value = ", ".join([os.fspath(p) for p in value])
        if not isinstance(value, (str, Path)):
            raise TypeError(
                f"value must be a string, or list/tuple of strings, got {type(value)}"
            )
        self.line_edit.value = os.fspath(Path(value).expanduser().absolute())

    def __repr__(self) -> str:
        return f"<LineEdit mode={self.mode.value!r}, value={self.value!r}>"
