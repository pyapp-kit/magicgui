"""# Callable functions demo

This example demonstrates handling callable functions with magicgui.
"""
from magicgui import magicgui


def f(x: int, y="a string") -> str:
    """Example function F."""
    return f"{y} {x}"


def g(x: int = 6, y="another string") -> str:
    """Example function G."""
    return f"{y} asdfsdf {x}"


@magicgui(call_button=True, func={"choices": ["f", "g"]})
def example(func="f"):
    """Ëxample function."""
    pass


def update(f: str):
    """Update function."""
    if len(example) > 2:
        del example[1]
    example.insert(1, magicgui(globals()[f]))


example.func.changed.connect(update)
example.show(run=True)
