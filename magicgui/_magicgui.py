from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional, Union, overload
from warnings import warn

if TYPE_CHECKING:
    from magicgui.application import AppRef
    from magicgui.widgets import FunctionGui


@overload
def magicgui(  # noqa
    function: Callable,
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    app: AppRef = None,
    **param_options: dict,
) -> FunctionGui:
    ...


@overload
def magicgui(  # noqa
    function=None,
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    app: AppRef = None,
    **param_options: dict,
) -> Callable[[Callable], FunctionGui]:
    ...


def magicgui(
    function: Optional[Callable] = None,
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    app: AppRef = None,
    **param_options: dict,
):
    """Return a :class:`FunctionGui` for ``function``.

    Parameters
    ----------
    function : Callable, optional
        The function to decorate.  Optional to allow bare decorator with optional
        arguments. by default ``None``
    layout : str, optional
        The type of layout to use. Must be one of {'horizontal', 'vertical'}.
        by default "horizontal".
    labels : bool, optional
        Whether labels are shown in the widget. by default True
    tooltips : bool, optional
        Whether tooltips are shown when hovering over widgets. by default True
    call_button : bool or str, optional
        If ``True``, create an additional button that calls the original function when
        clicked.  If a ``str``, set the button text. by default False
    auto_call : bool, optional
        If ``True``, changing any parameter in either the GUI or the widget attributes
        will call the original function with the current settings. by default False
    result_widget : bool, optional
        Whether to display a LineEdit widget the output of the function when called,
        by default False
    app : magicgui.Application or str, optional
        A backend to use, by default ``None`` (use the default backend.)

    **param_options : dict of dict
        Any additional keyword arguments will be used as parameter-specific options.
        Keywords MUST match the name of one of the arguments in the function
        signature, and the value MUST be a dict.

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
    if "result" in param_options:
        warn(
            "\n\nThe 'result' option is deprecated and will be removed in the future."
            "Please use `result_widget=True` instead.\n",
            FutureWarning,
        )

        param_options.pop("result")
        result_widget = True

    def inner_func(func: Callable) -> FunctionGui:
        from magicgui.widgets import FunctionGui

        func_gui = FunctionGui(
            function=func,
            call_button=call_button,
            layout=layout,
            labels=labels,
            tooltips=tooltips,
            param_options=param_options,
            auto_call=auto_call,
            result_widget=result_widget,
            app=app,
        )
        func_gui.__wrapped__ = func
        return func_gui

    if function is None:
        return inner_func
    else:
        return inner_func(function)