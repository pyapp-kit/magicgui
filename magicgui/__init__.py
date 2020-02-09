"""magicgui is a utility for generating a GUI from a python function"""

__author__ = """Talley Lambert"""
__email__ = "talley.lambert@gmail.com"
__version__ = "0.0.6"

from .core import magicgui
from . import _qt as api

event_loop = api.event_loop

__all__ = ["magicgui", "event_loop", "api"]
