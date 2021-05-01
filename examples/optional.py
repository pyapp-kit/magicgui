from pathlib import Path
from typing import Optional

from magicgui import magicgui


# Using optional will add a '----' to the combobox, which returns "None"
@magicgui
def f(path: Optional[Path] = None):
    print(path, type(path))


f.show(run=True)
