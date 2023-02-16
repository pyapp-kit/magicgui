import warnings
from typing import Any

from magicgui.widgets.bases._value_widget import ValueWidget  # noqa: F401

warnings.warn(
    "magicgui.widgets._bases is now public. "
    "Please import ValueWidget from magicgui.widgets.bases instead.",
    DeprecationWarning,
    stacklevel=2,
)


def __getattr__(name: str) -> Any:
    if name == "_Unset":
        from magicgui.types import _Undefined

        warnings.warn(
            "magicgui.widgets._bases.value_widget._Unset is removed. "
            "Use magicgui.types._Undefined instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return _Undefined
    if name == "UNSET":
        from magicgui.types import Undefined

        warnings.warn(
            "magicgui.widgets._bases.value_widget.UNSET is removed. "
            "Use magicgui.types.Undefined instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return Undefined

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
