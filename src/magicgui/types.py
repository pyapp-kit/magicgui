"""Types used internally in magicgui."""

from __future__ import annotations

from enum import Enum, EnumMeta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Literal, Tuple, Union

from typing_extensions import TypedDict

if TYPE_CHECKING:
    from magicgui.widgets import FunctionGui
    from magicgui.widgets.bases import CategoricalWidget, Widget
    from magicgui.widgets.protocols import WidgetProtocol


class ChoicesDict(TypedDict):
    """Dict Type for setting choices in a categorical widget."""

    choices: ChoicesIterable
    key: Callable[[Any], str]


#: A [`Widget`][magicgui.widgets.Widget] class or a
#: [`WidgetProtocol`][magicgui.widgets.protocols.WidgetProtocol]
WidgetClass = Union["type[Widget]", "type[WidgetProtocol]"]
#: A generic reference to a :attr:`WidgetClass` as a string, or the class itself.
WidgetRef = Union[str, WidgetClass]
#: A :attr:`WidgetClass` (or a string representation of one) and a dict of kwargs
WidgetTuple = Tuple[WidgetRef, Dict[str, Any]]
#: An iterable that can be used as a valid argument for widget ``choices``
ChoicesIterable = Union[Iterable[Tuple[str, Any]], Iterable[Any]]
#: An callback that can be used as a valid argument for widget ``choices``.  It takes
#: a categorical widget and returns a :attr:`ChoicesIterable`.
ChoicesCallback = Callable[["CategoricalWidget[Any]"], ChoicesIterable]
#: The set of all valid types for widget ``choices``.
ChoicesType = Union[EnumMeta, ChoicesIterable, ChoicesCallback, ChoicesDict]
#: A callback that may be registered for a given return annotation. When called, it will
#: be provided an instance of a
#: [~magicgui.widgets.FunctionGui][magicgui.widgets.FunctionGui],
#: the result of the function that was called, and the return annotation itself.
ReturnCallback = Callable[["FunctionGui", Any, type], None]
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


class _Undefined:
    """Sentinel class to indicate the lack of a value when ``None`` is ambiguous.

    ``_Undefined`` is a singleton.
    """

    _singleton: _Undefined | None = None

    def __new__(cls) -> _Undefined:
        if _Undefined._singleton is None:
            _Undefined._singleton = super().__new__(cls)
        return _Undefined._singleton

    def __repr__(self) -> str:
        return "..."

    def __bool__(self) -> bool:
        return False


Undefined = _Undefined()

JsonStringFormats = Literal[
    # ISO 8601 format.
    # https://www.iso.org/iso-8601-date-and-time-format.html
    "date-time",  # 2018-11-13T20:20:39+00:00
    "time",  # 20:20:39+00:00, Draft 7
    "date",  # 2018-11-13, Draft 7
    "duration",  # P1Y2M3DT4H5M6S, Draft 2019-09
    # email addresses
    "email",
    "idn-email",  # Draft 7
    # hostnames
    "hostname",  # internet host name, RFC 1123
    "idn-hostname",
    # ip addresses
    "ipv4",
    "ipv6",
    # resource identifiers
    "uuid",  # 3e4666bf-d5e5-4aa7-b8ce-cefe41c7568a, draft 2019-09
    "uri",  # RFC3986
    "uri-reference",  # RFC3986, section 4.1., draft 6
    "iri",  # draft 7
    "iri-reference",  # draft 7
    # uri template
    "uri-template",  # RFC6570, draft 6
    # json pointer
    "json-pointer",  # RFC6901, draft 6
    "relative-json-pointer",  # draft 7
    # regular expressions
    "regex",  # draft 7
]
