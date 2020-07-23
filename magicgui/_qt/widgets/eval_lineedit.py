"""A LineEdit widget that converts a literal string to a python object."""
from ast import literal_eval

from qtpy.QtWidgets import QLineEdit
from typing import Any


class LiteralEvalEdit(QLineEdit):
    """A LineEdit that returns the literal_eval() of the current text."""

    def text(self) -> Any:
        """Get current text and convert to python literal."""
        return literal_eval(super().text())
