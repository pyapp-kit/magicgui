import re
from enum import Enum, EnumMeta, auto


class FileDialogMode(Enum):
    """FileDialog mode options.

    EXISTING_FILE - returns one existing file.
    EXISTING_FILES - return one or more existing files.
    OPTIONAL_FILE - return one file name that does not have to exist.
    EXISTING_DIRECTORY - returns one existing directory.
    """

    EXISTING_FILE = "r"
    EXISTING_FILES = "rm"
    OPTIONAL_FILE = "w"
    EXISTING_DIRECTORY = "d"


def camel2snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def snake2camel(name):
    return "".join(word.title() for word in name.split("_"))


class _WidgetKindMeta(EnumMeta):
    def __call__(cls, value, *a, **kw):
        if isinstance(value, str):
            value = snake2camel(value) if "_" in value else value
        return super().__call__(value, *a, **kw)


class WidgetKind(Enum, metaclass=_WidgetKindMeta):
    """Known kinds of widgets.  CamelCase versions used for backend lookup."""

    def _generate_next_value_(name, start, count, last_values):
        return snake2camel(name)

    # Text
    LABEL = auto()
    LINE_EDIT = auto()
    TEXT_EDIT = auto()
    # Numbers
    SPIN_BOX = auto()
    FLOAT_SPIN_BOX = auto()
    SLIDER = auto()
    FLOAT_SLIDER = auto()
    LOG_SLIDER = auto()
    # SCROLL_BAR = auto()
    # Buttons
    PUSH_BUTTON = auto()
    CHECK_BOX = auto()
    RADIO_BUTTON = auto()
    # TOOL_BUTTON = auto()
    # Categorical
    COMBO_BOX = auto()
    # Dates
    DATE_TIME_EDIT = auto()
    TIME_EDIT = auto()
    DATE_EDIT = auto()
    # Paths
    FILE_EDIT = auto()

    @property
    def snake_name(self):
        """Return snake_case version of the name."""
        return camel2snake(self.value)
