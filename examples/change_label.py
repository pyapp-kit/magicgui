from magicgui import magicgui


@magicgui(x={"label": "A Label"})
def example(x=1, y="hi"):
    return x, y


example.changed.connect(lambda e: print(e.value))
example.show(run=True)
