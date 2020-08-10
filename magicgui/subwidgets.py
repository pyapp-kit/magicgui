import math
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar

from magicgui.base import BaseRangedWidget, BaseValueWidget

C = TypeVar("C")
F = TypeVar("F")

if TYPE_CHECKING:

    def lru_cache(f: F) -> F:
        pass


else:
    from functools import lru_cache


def transform_get_set(
    cls,
    get_transform: Optional[Callable[[Any], Any]] = None,
    set_transform: Optional[Callable[[Any], Any]] = None,
    prefix: str = "Transformed",
):
    if not issubclass(cls, BaseValueWidget):
        raise TypeError(
            "Class must implement `BaseValueWidget` to transform getter and setter."
        )
    suffixes = ["value"]
    if issubclass(cls, BaseRangedWidget):
        suffixes.extend(["maximum", "minimum", "step"])

    new_cls = type(f"{prefix}{cls.__name__}", (cls,), {"__module__": __name__})
    for suffix in suffixes:
        if get_transform:
            meth_name = f"_mg_get_{suffix}"
            old_getter = getattr(new_cls, meth_name, None)

            def new_getter(obj, old_getter=old_getter, transform=get_transform):
                return transform(old_getter(obj))

            setattr(new_cls, meth_name, new_getter)
        if set_transform:
            meth_name = f"_mg_set_{suffix}"
            old_setter = getattr(new_cls, meth_name, None)

            def new_setter(obj, val, old_setter=old_setter, transform=set_transform):
                old_setter(obj, transform(val))

            setattr(new_cls, meth_name, new_setter)
    return new_cls


FLOAT_PRECISION = 1000
LOG_BASE = math.e

make_float_class = lru_cache(
    partial(
        transform_get_set,
        get_transform=lambda x: x / FLOAT_PRECISION,
        set_transform=lambda x: int(x * FLOAT_PRECISION),
        prefix="Float",
    )
)

make_log_class = lru_cache(
    partial(
        transform_get_set,
        get_transform=lambda x: math.log(x / FLOAT_PRECISION, LOG_BASE),
        set_transform=lambda x: int(math.pow(LOG_BASE, x) * FLOAT_PRECISION),
        prefix="Float",
    )
)

MAP = {"Float": make_float_class, "Log": make_log_class}
