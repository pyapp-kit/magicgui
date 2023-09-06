"""# Optional user choice

Optional user input using a dropdown selection widget.
"""
from typing import Optional

from magicgui import magicgui


# Using optional will add a '----' to the combobox, which returns "None"
@magicgui(path={"choices": ["a", "b"]})
def f(path: Optional[str] = None):
    """Öptional user input function."""
    print(path, type(path))


f.show(run=True)
