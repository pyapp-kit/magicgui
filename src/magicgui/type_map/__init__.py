"""Functions that map python types to widgets."""

from ._type_map import get_widget_class, register_type, type2callback, type_registered

__all__ = [
    "get_widget_class",
    "register_type",
    "type_registered",
    "type2callback",
]
