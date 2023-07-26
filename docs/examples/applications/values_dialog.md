from magicgui.widgets import request_values

vals = request_values(
    age=int,
    name={"annotation": str, "label": "Enter your name:"},
    title="Hi, who are you?",
)
print(repr(vals))
