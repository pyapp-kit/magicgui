import warnings

from magicgui.widgets.bases import *  # noqa: F403

warnings.warn(
    "magicgui.widgets._bases has been made public. "
    "Please import from magicgui.widgets.bases instead.",
    DeprecationWarning,
    stacklevel=2,
)
