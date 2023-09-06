"""# Input values dialog

A basic example of a user input dialog.

This will pause code execution until the user responds.

# ![Values input dialog](../../images/values_input.png){ width=50% }

```python linenums="1"
from magicgui.widgets import request_values

vals = request_values(
    age=int,
    name={"annotation": str, "label": "Enter your name:"},
    title="Hi, who are you?",
)
print(repr(vals))
```
"""

# %%
