from typing import Optional

from magicgui import magicgui


# Using optional will add a '----' to the combobox, which returns "None"
@magicgui(path=dict(choices=["a", "b"]))
def f(path: Optional[str] = None):
    print(path, type(path))


f.show(run=True)
