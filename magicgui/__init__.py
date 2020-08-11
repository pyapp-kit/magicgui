"""magicgui is a utility for generating a GUI from a python function."""
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__author__ = """Talley Lambert"""
__email__ = "talley.lambert@gmail.com"


from .application import event_loop
from .decorator import magicgui

__all__ = ["magicgui", "register_type", "MagicGuiBase", "event_loop", "api"]
