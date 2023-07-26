from magicgui import magicgui


# use a different label than the default (the parameter name) in the UI
@magicgui(x={"label": "widget to set x"})
def example(x=1, y="hi"):
    return x, y


example.changed.connect(print)
example.show(run=True)
