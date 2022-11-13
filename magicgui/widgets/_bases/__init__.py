import warnings

from ..bases import *  # noqa: F401, F403

warnings.warn(
    "magicgui.widgets._bases has been made public. "
    "Please import from magicgui.widgets.bases instead.",
    DeprecationWarning,
    stacklevel=2,
)
