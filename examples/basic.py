from magicgui import magicgui


@magicgui
def example(x: int, y="hi"):
    return x, y


example.changed.connect(lambda e: print(e.value))
example.show(run=True)
