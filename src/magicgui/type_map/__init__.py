"""Functions that map python types to widgets."""

from typing import Any

from ._type_map import get_widget_class, register_type, type2callback, type_registered

__all__ = [
    "get_widget_class",
    "register_type",
    "type_registered",
    "type2callback",
]


def __getattr__(name: str) -> Any:
    """Import from magicgui.types if not found in magicgui.schema."""
    import warnings

    if name == "_type2callback":
        warnings.warn(
            "magicgui.type_map._type2callback is now public, "
            "use magicgui.type_map.type2callback",
            DeprecationWarning,
            stacklevel=2,
        )
        return type2callback
    if name == "pick_widget_type":
        from ._type_map import _pick_widget_type

        warnings.warn(
            "magicgui.type_map.pick_widget_type is deprecated, "
            "please use magicgui.type_map.get_widget_class instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return _pick_widget_type
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
