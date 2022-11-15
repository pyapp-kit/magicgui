import pytest
from typing_extensions import reveal_type


# fmt: off
@pytest.mark.mypy_testing
def magicgui_return_types() -> None:

    from magicgui import magicgui

    def f(a) -> str:
        return "hi"

    reveal_type(magicgui())  # R: def [_R] (def (*Any, **Any) -> _R`-1) -> magicgui.widgets._function_gui.FunctionGui[_R`-1]
    reveal_type(magicgui(f))  # R: magicgui.widgets._function_gui.FunctionGui[builtins.str]
    reveal_type(magicgui(f)())  # R: builtins.str
    reveal_type(magicgui(main_window=True))  # R: def [_R] (def (*Any, **Any) -> _R`-1) -> magicgui.widgets._function_gui.MainFunctionGui[_R`-1]
    reveal_type(magicgui(main_window=True)(f))  # R: magicgui.widgets._function_gui.MainFunctionGui[builtins.str]
    reveal_type(magicgui(main_window=True)(f)())  # R: builtins.str


@pytest.mark.mypy_testing
def magic_factory_return_types() -> None:
    from magicgui import magic_factory

    def f(a) -> str:
        return "hi"

    reveal_type(magic_factory())  # R: def [_R] (def (*Any, **Any) -> _R`-1) -> magicgui.type_map._magicgui.MagicFactory[magicgui.widgets._function_gui.FunctionGui[_R`-1]]
    reveal_type(magic_factory(f))  # R: magicgui.type_map._magicgui.MagicFactory[magicgui.widgets._function_gui.FunctionGui[builtins.str]]
    reveal_type(magic_factory(f)())  # R: magicgui.widgets._function_gui.FunctionGui[builtins.str]
    reveal_type(magic_factory(f)()())  # R: builtins.str
    reveal_type(magic_factory(main_window=True))  # R: def [_R] (def (*Any, **Any) -> _R`-1) -> magicgui.type_map._magicgui.MagicFactory[magicgui.widgets._function_gui.MainFunctionGui[_R`-1]]
    reveal_type(magic_factory(main_window=True)(f))  # R: magicgui.type_map._magicgui.MagicFactory[magicgui.widgets._function_gui.MainFunctionGui[builtins.str]]
    reveal_type(magic_factory(main_window=True)(f)())  # R: magicgui.widgets._function_gui.MainFunctionGui[builtins.str]
    reveal_type(magic_factory(main_window=True)(f)()())  # R: builtins.str
