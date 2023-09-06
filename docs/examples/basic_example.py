"""# Basic example

A basic example using magicgui.
"""
from magicgui import magicgui


@magicgui
def example(x: int, y="hi"):
    """Basic example function."""
    return x, y


example.changed.connect(print)
example.show(run=True)
