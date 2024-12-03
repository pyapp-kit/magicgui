from __future__ import annotations

import inspect
from functools import partial
from typing import Any, Callable, Generic, TypeVar

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

    def __getattr__(self, name: str) -> Any:
        """Allow accessing FunctionGui attributes without mypy error."""

    @property
    def __name__(self) -> str:
        """Pass function name."""
        return getattr(self.keywords.get("function"), "__name__", "FunctionGui")
