"""magicgui is a utility for generating a GUI from a python function."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("magicgui")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

__author__ = """Talley Lambert"""
__email__ = "talley.lambert@gmail.com"


from .application import event_loop, use_app
from .type_map import magic_factory, magicgui, register_type, type_registered

__all__ = [
    "event_loop",
    "magic_factory",
    "magicgui",
    "register_type",
    "type_registered",
    "use_app",
]


def __getattr__(name: str):
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
