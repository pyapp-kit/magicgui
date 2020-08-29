from enum import EnumMeta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, Optional, Tuple, Type, Union

from typing_extensions import TypedDict

if TYPE_CHECKING:
    from magicgui.function_gui import FunctionGui
    from magicgui.protocols import WidgetProtocol
    from magicgui.widgets import CategoricalWidget, FileDialogMode, Widget

WidgetClass = Union[Type["Widget"], Type["WidgetProtocol"]]
WidgetRef = Union[str, WidgetClass]
TypeMatcher = Callable[[Any, Optional[Type], Optional[dict]], WidgetRef]
ChoicesIterable = Union[Iterable[Tuple[str, Any]], Iterable[Any]]
ChoicesCallback = Callable[["CategoricalWidget"], ChoicesIterable]
ChoicesType = Union[EnumMeta, ChoicesIterable, ChoicesCallback, "ChoicesDict"]
ReturnCallback = Callable[["FunctionGui", Any, Type], None]
PathLike = Union[Path, str, bytes]


class ChoicesDict(TypedDict):
    """Dict Type for setting choices in a categorical widget."""

    choices: ChoicesIterable
    key: Callable[[Any], str]


class WidgetOptions(TypedDict, total=False):
    widget_type: WidgetRef
    choices: ChoicesType
    gui_only: bool
    visible: bool
    enabled: bool
    text: str
    minimum: float
    maximum: float
    step: float
    orientation: str
    mode: Union[str, "FileDialogMode"]
