from __future__ import annotations

import inspect
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Literal,
    TypeVar,
    cast,
    overload,
)

from magicgui.widgets import FunctionGui, MainFunctionGui

if TYPE_CHECKING:
    from typing_extensions import ParamSpec

    from magicgui.application import AppRef

    _P = ParamSpec("_P")

__all__ = ["magicgui", "magic_factory", "MagicFactory"]


_R = TypeVar("_R")
_FGuiVar = TypeVar("_FGuiVar", bound=FunctionGui)


@overload
def magicgui(
    function: Callable[_P, _R],
    *,
    layout: str = "horizontal",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[False] = False,
    app: AppRef | None = None,
    persist: bool = False,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> FunctionGui[_P, _R]: ...


@overload
def magicgui(
    function: Literal[None] | None = None,
    *,
    layout: str = "horizontal",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[False] = False,
    app: AppRef | None = None,
    persist: bool = False,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> Callable[[Callable[_P, _R]], FunctionGui[_P, _R]]: ...


@overload
def magicgui(
    function: Callable[_P, _R],
    *,
    layout: str = "horizontal",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[True],
    app: AppRef | None = None,
    persist: bool = False,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> MainFunctionGui[_P, _R]: ...


@overload
def magicgui(
    function: Literal[None] | None = None,
    *,
    layout: str = "horizontal",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[True],
    app: AppRef | None = None,
    persist: bool = False,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> Callable[[Callable[_P, _R]], MainFunctionGui[_P, _R]]: ...


def magicgui(
    function: Callable | None = None,
    *,
    layout: str = "vertical",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: bool = False,
    app: AppRef | None = None,
    persist: bool = False,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> Callable | FunctionGui:
    """Return a [`FunctionGui`][magicgui.widgets.FunctionGui] for `function`.

    Parameters
    ----------
    function : Callable, optional
        The function to decorate.  Optional to allow bare decorator with optional
        arguments. by default ``None``
    layout : str, optional
        The type of layout to use. Must be `horizontal` or `vertical`
        by default "vertical".
    scrollable : bool, optional
        Whether to enable scroll bars or not. If enabled, scroll bars will
        only appear along the layout direction, not in both directions.
    labels : bool, optional
        Whether labels are shown in the widget. by default True
    tooltips : bool, optional
        Whether tooltips are shown when hovering over widgets. by default True
    call_button : bool or str, optional
        If ``True``, create an additional button that calls the original
        function when clicked.  If a ``str``, set the button text. If None (the
        default), it defaults to True when ``auto_call`` is False, and False
        otherwise.
    auto_call : bool, optional
        If ``True``, changing any parameter in either the GUI or the widget attributes
        will call the original function with the current settings. by default False
    result_widget : bool, optional
        Whether to display a LineEdit widget the output of the function when called,
        by default False
    main_window : bool
        Whether this widget should be treated as the main app window, with menu bar,
        by default False.
    app : magicgui.Application or str, optional
        A backend to use, by default ``None`` (use the default backend.)
    persist : bool, optional
        If `True`, when parameter values change in the widget, they will be stored to
        disk and restored when the widget is loaded again with ``persist = True``.
        Call ``magicgui._util.user_cache_dir()`` to get the default cache location.
        By default False.
    raise_on_unknown : bool, optional
        If ``True``, raise an error if magicgui cannot determine widget for function
        argument or return type. If ``False``, ignore unknown types. By default False.
    param_options : dict[str, dict]
        Any additional keyword arguments will be used as parameter-specific options.
        Keywords must match the name of one of the arguments in the function signature,
        and the value must be a dict of keyword arguments to pass to the widget
        constructor.

    Returns
    -------
    result : FunctionGui or Callable[[F], FunctionGui]
        If ``function`` is not ``None`` (such as when this is used as a bare decorator),
        returns a FunctionGui instance, which is a list-like container of autogenerated
        widgets corresponding to each parameter in the function.
        If ``function`` is ``None`` such as when arguments are provided like
        ``magicgui(auto_call=True)``, then returns a function that can be used as a
        decorator.

    Examples
    --------
    >>> @magicgui
    ... def my_function(a: int = 1, b: str = 'hello'):
    ...     pass
    ...
    >>> my_function.show()
    >>> my_function.a.value == 1  # True
    >>> my_function.b.value = 'world'
    """
    return _magicgui(
        function=function,
        layout=layout,
        scrollable=scrollable,
        labels=labels,
        tooltips=tooltips,
        call_button=call_button,
        auto_call=auto_call,
        result_widget=result_widget,
        main_window=main_window,
        app=app,
        persist=persist,
        raise_on_unknown=raise_on_unknown,
        param_options=param_options,
    )


@overload
def magic_factory(
    function: Callable[_P, _R],
    *,
    layout: str = "horizontal",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[False] = False,
    app: AppRef | None = None,
    persist: bool = False,
    widget_init: Callable[[FunctionGui], None] | None = None,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> MagicFactory[FunctionGui[_P, _R]]: ...


@overload
def magic_factory(
    function: Literal[None] | None = None,
    *,
    layout: str = "horizontal",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[False] = False,
    app: AppRef | None = None,
    persist: bool = False,
    widget_init: Callable[[FunctionGui], None] | None = None,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> Callable[[Callable[_P, _R]], MagicFactory[FunctionGui[_P, _R]]]: ...


@overload
def magic_factory(
    function: Callable[_P, _R],
    *,
    layout: str = "horizontal",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[True],
    app: AppRef | None = None,
    persist: bool = False,
    widget_init: Callable[[FunctionGui], None] | None = None,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> MagicFactory[MainFunctionGui[_P, _R]]: ...


@overload
def magic_factory(
    function: Literal[None] | None = None,
    *,
    layout: str = "horizontal",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[True],
    app: AppRef | None = None,
    persist: bool = False,
    widget_init: Callable[[FunctionGui], None] | None = None,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> Callable[[Callable[_P, _R]], MagicFactory[MainFunctionGui[_P, _R]]]: ...


def magic_factory(
    function: Callable | None = None,
    *,
    layout: str = "vertical",
    scrollable: bool = False,
    labels: bool = True,
    tooltips: bool = True,
    call_button: bool | str | None = None,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: bool = False,
    app: AppRef | None = None,
    persist: bool = False,
    widget_init: Callable[[FunctionGui], None] | None = None,
    raise_on_unknown: bool = False,
    **param_options: dict,
) -> Callable | MagicFactory:
    """Return a [`MagicFactory`][magicgui.type_map._magicgui.MagicFactory] for function.

    `magic_factory` is nearly identical to the [`magicgui`][magicgui.magicgui] decorator
    with the following differences:

    1. Whereas `magicgui` returns a `FunctionGui` instance, `magic_factory` returns a
       callable that returns a `FunctionGui` instance.  (Technically, it returns an
       instance of [`MagicFactory`][magicgui.type_map._magicgui.MagicFactory] which you
       behaves exactly like a [`functools.partial`][functools.partial]
       for a `FunctionGui` instance.)
    2. `magic_factory` adds a `widget_init` method: a callable that will be called
        immediately after the `FunctionGui` instance is created.  This can be used to
        add additional widgets to the layout, or to connect signals to the widgets.

    !!!important
        Whereas decorating a function with `magicgui` will **immediately** create a
        widget instance, `magic_factory` will **not** create a widget instance until the
        decorated object is called.  This is often what you want in a library, whereas
        `magicgui` is useful for rapid, interactive development.

    Parameters
    ----------
    function : Callable, optional
        The function to decorate.  Optional to allow bare decorator with optional
        arguments. by default ``None``
    layout : str, optional
        The type of layout to use. Must be `horizontal` or `vertical`
        by default "vertical".
    scrollable : bool, optional
        Whether to enable scroll bars or not. If enabled, scroll bars will
        only appear along the layout direction, not in both directions.
    labels : bool, optional
        Whether labels are shown in the widget. by default True
    tooltips : bool, optional
        Whether tooltips are shown when hovering over widgets. by default True
    call_button : bool or str, optional
        If ``True``, create an additional button that calls the original
        function when clicked.  If a ``str``, set the button text. If None (the
        default), it defaults to True when ``auto_call`` is False, and False
        otherwise.
    auto_call : bool, optional
        If ``True``, changing any parameter in either the GUI or the widget attributes
        will call the original function with the current settings. by default False
    result_widget : bool, optional
        Whether to display a LineEdit widget the output of the function when called,
        by default False
    main_window : bool
        Whether this widget should be treated as the main app window, with menu bar,
        by default False.
    app : magicgui.Application or str, optional
        A backend to use, by default ``None`` (use the default backend.)
    persist : bool, optional
        If `True`, when parameter values change in the widget, they will be stored to
        disk and restored when the widget is loaded again with ``persist = True``.
        Call ``magicgui._util.user_cache_dir()`` to get the default cache location.
        By default False.
    widget_init : callable, optional
        A function that will be called with the newly created widget instance as its
        only argument.  This can be used to customize the widget after it is created.
        by default ``None``.
    raise_on_unknown : bool, optional
        If ``True``, raise an error if magicgui cannot determine widget for function
        argument or return type. If ``False``, ignore unknown types. By default False.
    param_options : dict of dict
        Any additional keyword arguments will be used as parameter-specific widget
        options. Keywords must match the name of one of the arguments in the function
        signature, and the value must be a dict of keyword arguments to pass to the
        widget constructor.

    Returns
    -------
    result : MagicFactory or Callable[[F], MagicFactory]
        If ``function`` is not ``None`` (such as when this is used as a bare decorator),
        returns a MagicFactory instance.
        If ``function`` is ``None`` such as when arguments are provided like
        ``magic_factory(auto_call=True)``, then returns a function that can be used as a
        decorator.

    Examples
    --------
    >>> @magic_factory
    ... def my_function(a: int = 1, b: str = 'hello'):
    ...     pass
    ...
    >>> my_widget = my_function()
    >>> my_widget.show()
    >>> my_widget.a.value == 1  # True
    >>> my_widget.b.value = 'world'
    """
    return _magicgui(
        factory=True,
        function=function,
        layout=layout,
        scrollable=scrollable,
        labels=labels,
        tooltips=tooltips,
        call_button=call_button,
        auto_call=auto_call,
        result_widget=result_widget,
        main_window=main_window,
        app=app,
        persist=persist,
        widget_init=widget_init,
        raise_on_unknown=raise_on_unknown,
        param_options=param_options,
    )


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
    ...
    >>> factory = MagicFactory(function=func, labels=False)
    >>> # factory accepts all the same arguments as magicgui()
    >>> widget1 = factory(call_button=True)
    >>> # can also override magic_kwargs that were provided when creating the factory
    >>> widget2 = factory(auto_call=True, labels=True)
    """

    _widget_init: Callable[[_FGuiVar], None] | None = None
    # func here is the function that will be called to create the widget
    # i.e. it will be either the FunctionGui or MainFunctionGui class
    func: Callable[..., _FGuiVar]

    def __new__(
        cls,
        function: Callable,
        *args: Any,
        magic_class: type[_FGuiVar] = FunctionGui,  # type: ignore
        widget_init: Callable[[_FGuiVar], None] | None = None,
        **keywords: Any,
    ) -> MagicFactory:
        """Create new MagicFactory."""
        if function is None:
            raise TypeError(
                "MagicFactory missing required positional argument 'function'"
            )

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
        obj = super().__new__(cls, magic_class, *args, **keywords)  # type: ignore
        obj._widget_init = widget_init
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
        widget = self.func(param_options=prm_options, **{**factory_kwargs, **kwargs})
        if self._widget_init is not None:
            self._widget_init(widget)
        return widget

    def __getattr__(self, name: str) -> Any:
        """Allow accessing FunctionGui attributes without mypy error."""

    @property
    def __name__(self) -> str:
        """Pass function name."""
        return getattr(self.keywords.get("function"), "__name__", "FunctionGui")


def _magicgui(
    function: Callable | None = None,
    factory: bool = False,
    widget_init: Callable | None = None,
    main_window: bool = False,
    **kwargs: Any,
) -> Callable:
    """Actual private magicui decorator.

    if factory is `True` will return a MagicFactory instance, that can be called
    to return a `FunctionGui` instance.  See docstring of ``magicgui`` for parameters.
    Otherwise, this will return a FunctionGui instance directly.
    """

    def inner_func(func: Callable) -> FunctionGui | MagicFactory:
        if not callable(func):
            raise TypeError("the first argument must be callable")

        magic_class = MainFunctionGui if main_window else FunctionGui

        if factory:
            return MagicFactory(
                func, magic_class=magic_class, widget_init=widget_init, **kwargs
            )
        # MagicFactory is unnecessary if we are immediately instantiating the widget,
        # so we shortcut that and just return the FunctionGui here.
        return cast(FunctionGui, magic_class(func, **kwargs))

    return inner_func if function is None else inner_func(function)
