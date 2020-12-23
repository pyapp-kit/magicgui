---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.12
    jupytext_version: 1.7.1
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Direct Widget API

While the primary API is to use the {func}`@magicgui <magicgui.magicgui>`
decorator, one can also instantiate widgets directly using any of the widgets in
{mod}`magicgui.widgets`.

Generally, one will construct a {class}`~magicgui.widgets.Container` object that
acts as a layout for all of the sub-widgets.

```{code-cell} python
from magicgui.widgets import SpinBox, FileEdit, Slider, Label, Container
from pathlib import Path

# make some widgets
spin_box = SpinBox(value=10, name='spin', label='Value:', max=100)
file_picker = FileEdit(value='some/path')
slider = Slider(value=30, min=20, max=40)
label = Label(value=slider.value)

# set up callbacks
def set_label(event):
    label.value = event.value

slider.changed.connect(set_label)

# create a container to hold the widgets:
container = Container(widgets=[spin_box, file_picker, slider, label])
container.show()
```

Note, {class}`~magicgui.widgets.Container` widgets are subclassed from python's
{class}`collections.abc.MutableSequence`, so they behave like a basic python
list.  You can `append`, `instert`, `pop` widgets as you would with a regular
list:

```python
container.remove(file_picker)
container.pop(0)
container.insert(2, Label(value='a new label'))
container.show()
```
