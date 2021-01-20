"""magicgui is a utility for generating a GUI from a python function."""
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__author__ = """Talley Lambert"""
__email__ = "talley.lambert@gmail.com"


from ._magicgui import magicgui
from .application import event_loop, use_app
from .type_map import register_type

__all__ = [
    "event_loop",
    "magicgui",
    "register_type",
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
