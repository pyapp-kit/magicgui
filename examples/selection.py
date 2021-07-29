from magicgui import magicgui


@magicgui(
    pick_some={
        "choices": ["first", "second", "third", "fourth"],
        "allow_multiple": True,
    }
)
def my_widget(pick_some=["first"]):
    pass


my_widget.show(run=True)
