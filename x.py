from magicgui import use_app, widgets

app = use_app("textual")
l1 = widgets.Label(value="Hello World")
l2 = widgets.LineEdit(value="Hello World")
app.run()
