"""Types used internally in magicgui."""
from enum import Enum, EnumMeta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional, Tuple, Type, Union

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
#: A :attr:`WidgetClass` (or a string representation of one) and a dict of appropriate
#: :class:`WidgetOptions`.
WidgetTuple = Tuple[WidgetRef, "WidgetOptions"]
#: A function that takes a ``(value, annotation)`` argument and returns an optional
#: :attr:`WidgetTuple`
TypeMatcher = Callable[[Any, Optional[Type]], Optional[WidgetTuple]]
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


class WidgetOptions(TypedDict, total=False):
    """Recognized options when instantiating a Widget.

    .. note::

       this should be improved to be widget-type specific.
    """

    widget_type: WidgetRef
    choices: ChoicesType
    gui_only: bool
    visible: bool
    enabled: bool
    text: str
    min: float
    max: float
    step: float
    layout: str  # for things like containers
    orientation: str  # for things like sliders
    mode: Union[str, FileDialogMode]
    tooltip: str
    bind: Any
