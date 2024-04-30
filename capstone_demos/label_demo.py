from magicgui import magicgui


@magicgui(x={"label": "TEST", "label_min_width": 100, "label_min_height": 100, "label_max_width": 200, "label_max_height": 200})
def example(x="test"):
    return x

@magicgui(
    pick_some={
        "choices": ("first", "second", "third", "fourth"),
        "allow_multiple": True, "label_max_height": 500, "label_max_width": 500
    }
)
def my_widget(pick_some=("first")):
    """Dropdown selection function."""
    print("you selected", pick_some)


my_widget.show(run=True)
example.show(run=True)
