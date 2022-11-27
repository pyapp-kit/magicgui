"""magicgui is a utility for generating a GUI from a python function."""
from importlib.metadata import PackageNotFoundError, version
from typing import Any

try:
    __version__ = version("magicgui")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "uninstalled"

__author__ = """Talley Lambert"""
__email__ = "talley.lambert@gmail.com"


from .application import event_loop, use_app
from .type_map import register_type, type_registered
from .type_map._magicgui import magic_factory, magicgui

__all__ = [
    "event_loop",
    "magic_factory",
    "magicgui",
    "register_type",
    "type_registered",
    "use_app",
]


def __getattr__(name: str) -> Any:
    if name == "FunctionGui":
        from warnings import warn

        from .widgets import FunctionGui

        warn(
            "magicgui.FunctionGui is deprecated. "
            "Please import at magicgui.widgets.FunctionGui",
            DeprecationWarning,
            stacklevel=2,
        )

        return FunctionGui
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def compare(this: str, other: str = "other", *x: str) -> int:
    """Compare two version strings.

    Return negative if this < other, 0 if this == other, positive if this > other.

    Parameters
    ----------
    this : str
        Version string to compare.
    other : str
        Version string to compare.
    x: str
        Additional version strings to compare.

    Other Parameters
    ----------------
    version : str
        Version string to compare.

    Returns
    -------
    int
        Negative if this < other, 0 if this == other, positive if this > other.

    Examples
    --------
    >>> compare('0.1.0', '0.1.0')
    0
    >>> compare('0.1.0', '0.1.1')
    -1
    """
    this = this.split(".")
    other = other.split(".")
    for _i, (a, b) in enumerate(zip(this, other)):
        if a != b:
            return int(a) - int(b)
    return len(this) - len(other)
