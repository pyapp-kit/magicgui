"""Types used internally in magicgui."""
from __future__ import annotations

from enum import Enum, EnumMeta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Tuple, Type, Union

from typing_extensions import TypedDict

if TYPE_CHECKING:
    from magicgui.widgets import FunctionGui
    from magicgui.widgets._bases import CategoricalWidget, Widget
    from magicgui.widgets._protocols import WidgetProtocol

#: A :class:`~magicgui.widgets._bases.Widget` class or a
#: :class:`~magicgui.widgets._protocols.WidgetProtocol`
WidgetClass = Union[Type["Widget"], Type["WidgetProtocol"]]
#: A generic reference to a :attr:`WidgetClass` as a string, or the class itself.
WidgetRef = Union[str, WidgetClass]
#: A :attr:`WidgetClass` (or a string representation of one) and a dict of kwargs
WidgetTuple = Tuple[WidgetRef, dict]
#: An iterable that can be used as a valid argument for widget ``choices``
ChoicesIterable = Union[Iterable[Tuple[str, Any]], Iterable[Any]]
#: An callback that can be used as a valid argument for widget ``choices``.  It takes
#: a categorical widget and returns a :attr:`ChoicesIterable`.
ChoicesCallback = Callable[["CategoricalWidget"], ChoicesIterable]
#: The set of all valid types for widget ``choices``.
ChoicesType = Union[EnumMeta, ChoicesIterable, ChoicesCallback, "ChoicesDict"]
#: A callback that may be registered for a given return annotation. When called, it will
#: be provided an instance of a :class:`~magicgui.widgets.FunctionGui`, the result
#: of the function that was called, and the return annotation itself.
ReturnCallback = Callable[["FunctionGui", Any, Type], None]
#: A valid file path type
PathLike = Union[Path, str, bytes]


class FileDialogMode(Enum):
    """FileDialog mode options.

    - ``EXISTING_FILE`` - returns one existing file.
    - ``EXISTING_FILES`` - return one or more existing files.
    - ``OPTIONAL_FILE`` - return one file name that does not have to exist.
    - ``EXISTING_DIRECTORY`` - returns one existing directory.
    """

    EXISTING_FILE = "r"
    EXISTING_FILES = "rm"
    OPTIONAL_FILE = "w"
    EXISTING_DIRECTORY = "d"


class ChoicesDict(TypedDict):
    """Dict Type for setting choices in a categorical widget."""

    choices: ChoicesIterable
    key: Callable[[Any], str]


class _Undefined:
    """Sentinel class to indicate the lack of a value when ``None`` is ambiguous.

    ``_Undefined`` is a singleton.
    """

    _singleton = None

    def __new__(cls):
        if _Undefined._singleton is None:
            _Undefined._singleton = super().__new__(cls)
        return _Undefined._singleton

    def __repr__(self):
        return "<Undefined>"

    def __bool__(self):
        return False


Undefined = _Undefined()
