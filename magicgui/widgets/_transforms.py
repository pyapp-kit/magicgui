import math
from ast import literal_eval
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Optional

from magicgui.widgets._protocols import RangedWidgetProtocol, ValueWidgetProtocol

if TYPE_CHECKING:

    def lru_cache(maxsize: int = 128) -> Callable:  # noqa: D103
        pass


else:
    from functools import lru_cache


def transform_get_set(
    cls,
    get_transform: Optional[Callable[[Any], Any]] = None,
    set_transform: Optional[Callable[[Any], Any]] = None,
    prefix: str = "Transformed",
):
    """Overly complicated decorator to transform the get/set methods of a class."""
    if isinstance(cls, str):
        from magicgui.application import use_app

        app = use_app()
        assert app.native
        cls = app.get_obj(cls)
    if not issubclass(cls, ValueWidgetProtocol):
        raise TypeError(
            "Class must implement `BaseValueWidget` to transform getter and setter."
        )
    suffixes = ["value"]
    if issubclass(cls, RangedWidgetProtocol):
        suffixes.extend(["max", "min", "step"])

    new_cls = type(f"{prefix}{cls.__name__}", (cls,), {"__module__": __name__})
    for suffix in suffixes:
        if get_transform:
            meth_name = f"_mgui_get_{suffix}"
            old_getter = getattr(new_cls, meth_name, None)

            def new_getter(obj, old_getter=old_getter, transform=get_transform):
                return transform(old_getter(obj))

            setattr(new_cls, meth_name, new_getter)
        if set_transform:
            meth_name = f"_mgui_set_{suffix}"
            old_setter = getattr(new_cls, meth_name, None)

            def new_setter(obj, val, old_setter=old_setter, transform=set_transform):
                old_setter(obj, transform(val))

            setattr(new_cls, meth_name, new_setter)
    return new_cls


# TODO: make these accessible from the instance again without losing this pattern.

FLOAT_PRECISION = 1000
LOG_BASE = math.e

make_float = lru_cache(maxsize=32)(
    partial(
        transform_get_set,
        get_transform=lambda x: x / FLOAT_PRECISION,
        set_transform=lambda x: int(x * FLOAT_PRECISION),
        prefix="Float",
    )
)


def _literal_eval(x):
    if x == "":
        return ""
    elif x.lower == "none":
        return None
    return literal_eval(x)


make_literal_eval = lru_cache(maxsize=32)(
    partial(transform_get_set, get_transform=_literal_eval, prefix="LiteralEval"),
)
