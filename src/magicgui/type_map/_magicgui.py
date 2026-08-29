from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import partial
from typing import Any, Generic, TypeVar

from magicgui.type_map._type_map import TypeMap
from magicgui.widgets import FunctionGui

__all__ = ["MagicFactory", "magic_factory", "magicgui"]

_FGuiVar = TypeVar("_FGuiVar", bound=FunctionGui)

magicgui = TypeMap.global_instance().magicgui
magic_factory = TypeMap.global_instance().magic_factory

MAGICGUI_PARAMS = inspect.signature(magicgui).parameters


# _R is the return type of the decorated function
# _T is the type of the FunctionGui instance (FunctionGui or MainFunctionGui)
class MagicFactory(partial, Generic[_FGuiVar]):
    """Factory function that returns a FunctionGui instance.

    While this can be used directly, (see example below) the preferred usage is
    via the [`magicgui.magic_factory`][magicgui.magic_factory] decorator.

    Examples
    --------
    >>> def func(x: int, y: str):
    ...     pass
    >>> factory = MagicFactory(function=func, labels=False)
    >>> # factory accepts all the same arguments as magicgui()
    >>> widget1 = factory(call_button=True)
    >>> # can also override magic_kwargs that were provided when creating the factory
    >>> widget2 = factory(auto_call=True, labels=True)
    """

    _widget_init: Callable[[_FGuiVar], None] | None = None
    _type_map: TypeMap
    # func here is the function that will be called to create the widget
    # i.e. it will be either the FunctionGui or MainFunctionGui class
    func: Callable[..., _FGuiVar]

    def __new__(
        cls,
        function: Callable,
        *args: Any,
        magic_class: type[_FGuiVar] = FunctionGui,  # type: ignore
        widget_init: Callable[[_FGuiVar], None] | None = None,
        type_map: TypeMap | None = None,
        **keywords: Any,
    ) -> MagicFactory:
        """Create new MagicFactory."""
        if function is None:
            raise TypeError(
                "MagicFactory missing required positional argument 'function'"
            )
        if type_map is None:
            type_map = TypeMap.global_instance()
        # we want function first for the repr
        keywords = {"function": function, **keywords}
        if widget_init is not None:
            if not callable(widget_init):
                raise TypeError(
                    f"'widget_init' must be a callable, not {type(widget_init)}"
                )
            if len(inspect.signature(widget_init).parameters) != 1:
                raise TypeError(
                    "'widget_init' must be a callable that accepts a single argument"
                )
        obj = super().__new__(cls, magic_class, *args, **keywords)
        obj._widget_init = widget_init
        obj._type_map = type_map
        return obj

    def __repr__(self) -> str:
        """Return string repr."""
        args = [
            f"{k}={v!r}"
            for (k, v) in self.keywords.items()
            if v not in (MAGICGUI_PARAMS[k].default, {})
        ]
        return f"MagicFactory({', '.join(args)})"

    # TODO: annotate args and kwargs here so that
    # calling a MagicFactory instance gives proper mypy hints
    def __call__(self, *args: Any, **kwargs: Any) -> _FGuiVar:
        """Call the wrapped _magicgui and return a FunctionGui."""
        if args:
            raise ValueError("MagicFactory instance only accept keyword arguments")

        factory_kwargs = self.keywords.copy()
        prm_options = factory_kwargs.pop("param_options", {})
        prm_options.update(
            {k: kwargs.pop(k) for k in list(kwargs) if k not in MAGICGUI_PARAMS}
        )
        widget = self.func(
            param_options=prm_options,
            type_map=self._type_map,
            **{**factory_kwargs, **kwargs},
        )
        if self._widget_init is not None:
            self._widget_init(widget)
        return widget

    def __get__(self, obj: object, objtype: type | None = None) -> MagicFactory:
        """Provide descriptor protocol.

        This allows the `@magic_factory` decorator to work on a method as well as
        on a plain function.  Accessing the attribute on an instance returns a
        factory whose widgets bind the first parameter of the function to that
        instance, mirroring `FunctionGui.__get__`.

        Without this, `functools.partial.__get__` (added in Python 3.13) would
        bind the instance as the first *positional* argument of the factory,
        while on older versions the instance was simply never passed at all.
        """
        if obj is None:
            return self
        function = self.keywords.get("function")
        if function is None:  # pragma: no cover
            return self
        p0 = next(iter(inspect.signature(function).parameters), None)
        if p0 is None:  # pragma: no cover
            return self
        keywords = self.keywords.copy()
        param_options = dict(keywords.pop("param_options", None) or {})
        param_options.setdefault(p0, {"bind": obj})
        return type(self)(
            magic_class=self.func,  # type: ignore
            widget_init=self._widget_init,
            type_map=self._type_map,
            param_options=param_options,
            **keywords,
        )

    def __getattr__(self, name: str) -> Any:
        """Allow accessing FunctionGui attributes without mypy error."""

    @property
    def __name__(self) -> str:
        """Pass function name."""
        return getattr(self.keywords.get("function"), "__name__", "FunctionGui")
