"""magicgui is a utility for generating a GUI from a python function."""
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

__author__ = """Talley Lambert"""
__email__ = "talley.lambert@gmail.com"


from . import _qt as api
from .core import MagicGuiBase, magicgui, register_type

event_loop = api.event_loop

__all__ = ["magicgui", "register_type", "MagicGuiBase", "event_loop", "api"]
