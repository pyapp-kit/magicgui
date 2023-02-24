from magicgui import use_app, widgets

app = use_app("textual")
l1 = widgets.Label(value="I'm a label")
l2 = widgets.LineEdit(value="I'm a line edit")
btn = widgets.PushButton(text="I'm a button")
chx = widgets.CheckBox(text="I'm a checkbox")


@l2.changed.connect
def _on_click(newval) -> None:
    print("line edit changed", newval)


@btn.clicked.connect
def _on_click() -> None:
    print("Button clicked!")


@chx.changed.connect
def _on_click(newval) -> None:
    print("Checkbox changed", newval)
    btn.enabled = not newval


app.run()
