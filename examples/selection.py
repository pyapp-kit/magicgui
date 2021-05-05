from magicgui import magicgui


@magicgui(pick_one={"choices": ["first", "second", "third"], "allow_multiple": True})
def my_widget(pick_one="first"):
    pass


my_widget.show(run=True)
