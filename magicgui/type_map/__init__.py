"""Functions that map python types to widgets."""

from ._magicgui import MagicFactory, magic_factory, magicgui
from ._type_map import (
    get_widget_class,
    pick_widget_type,
    register_type,
    type2callback,
    type_registered,
)

__all__ = [
    "get_widget_class",
    "register_type",
    "type_registered",
    "type2callback",
    "MagicFactory",
    "magicgui",
    "pick_widget_type",
    "magic_factory",
]


def __getattr__(name: str):
    """Import from magicgui.types if not found in magicgui.schema."""
    if name == "_type2callback":
        import warnings

        warnings.warn(
            "magicgui.type_map._type2callback is now public, "
            "use magicgui.type_map.type2callback",
            DeprecationWarning,
            stacklevel=2,
        )
        return type2callback
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
