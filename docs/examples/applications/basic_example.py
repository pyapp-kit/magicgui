from magicgui import magicgui


@magicgui
def example(x: int, y="hi"):
    return x, y


example.changed.connect(print)
example.show(run=True)
