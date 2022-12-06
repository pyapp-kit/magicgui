import warnings

from magicgui.widgets.bases._widget import Widget  # noqa: F401

warnings.warn(
    "magicgui.widgets._bases._widget is removed. "
    "Please import Widget from magicgui.widgets.bases instead.",
    DeprecationWarning,
    stacklevel=2,
)
