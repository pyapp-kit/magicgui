from magicgui import magicgui


@magicgui
def example(x=1, y="hi"):
    return x, y


example.widgets.changed.connect(lambda e: print(e.value))
example.show(run=True)
