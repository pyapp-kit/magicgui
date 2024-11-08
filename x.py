from typing import Any, Optional

from magicgui import magicgui, register_type
from magicgui.widgets import FunctionGui


class Thing: ...


def on_thing_received(wdg: FunctionGui, thing: Any, type_: type) -> None:
    print(f"Received a {type_}:", thing)


register_type(Thing, return_callback=on_thing_received)


@magicgui
def my_widget() -> Optional[Thing]:
    return Thing()


my_widget()
