"""Functions that map python types to widgets."""

from ._type_map import (
    TypeMap,
    get_widget_class,
    register_type,
    type2callback,
    type_registered,
)

__all__ = [
    "TypeMap",
    "get_widget_class",
    "register_type",
    "type2callback",
    "type_registered",
]
