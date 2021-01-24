from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, Union, overload

from typing_extensions import Literal

if TYPE_CHECKING:
    from magicgui.application import AppRef
    from magicgui.widgets import FunctionGui, MainFunctionGui

_T = TypeVar("_T")
_R = TypeVar("_R")

class MagicFactory(partial, Generic[_T]):
    def __new__(cls, function, *args, magic_class=FunctionGui, **keywords):
        MagicFactory
    def __repr__(self) -> str: ...
    def __call__(self, *args, **kwargs) -> _T: ...
    def __getattr__(self, name: str) -> Any: ...
    @property
    def __name__(self) -> str: ...

@overload
def magicgui(  # noqa
    function: Callable[..., _R],
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[False] = False,
    app: AppRef = None,
    **param_options: dict,
) -> FunctionGui[_R]: ...
@overload  # noqa: E302
def magicgui(  # noqa
    function: Literal[None] = None,
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[False] = False,
    app: AppRef = None,
    **param_options: dict,
) -> Callable[[Callable[..., _R]], FunctionGui[_R]]: ...
@overload  # noqa: E302
def magicgui(  # noqa
    function: Callable[..., _R],
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[True],
    app: AppRef = None,
    **param_options: dict,
) -> MainFunctionGui[_R]: ...
@overload  # noqa: E302
def magicgui(  # noqa
    function=None,
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[True],
    app: AppRef = None,
    **param_options: dict,
) -> Callable[[Callable[..., _R]], MainFunctionGui[_R]]: ...
@overload  # noqa: E302
def magic_factory(  # noqa
    function: Callable[..., _R],
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[False] = False,
    app: AppRef = None,
    **param_options: dict,
) -> MagicFactory[FunctionGui[_R]]: ...
@overload  # noqa: E302
def magic_factory(  # noqa
    function: Literal[None] = None,
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[False] = False,
    app: AppRef = None,
    **param_options: dict,
) -> Callable[[Callable[..., _R]], MagicFactory[FunctionGui[_R]]]: ...
@overload  # noqa: E302
def magic_factory(  # noqa
    function: Callable[..., _R],
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[True],
    app: AppRef = None,
    **param_options: dict,
) -> MagicFactory[MainFunctionGui[_R]]: ...
@overload  # noqa: E302
def magic_factory(  # noqa
    function: Literal[None] = None,
    *,
    layout: str = "horizontal",
    labels: bool = True,
    tooltips: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    main_window: Literal[True],
    app: AppRef = None,
    **param_options: dict,
) -> Callable[[Callable[..., _R]], MagicFactory[MainFunctionGui[_R]]]: ...
