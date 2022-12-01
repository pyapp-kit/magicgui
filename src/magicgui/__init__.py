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
