# configuration

If used without arguments, the `@magicgui` decorator will build you a GUI using the
default settings.  However, `magicgui` also accepts a number of options to configure your
GUI:

## `magicgui` options

### `call_button`

If a `call_button` argument is provided that evaluates to `True`, a button will be added
to the gui which, when clicked, will call the decorated function with the current values
from the gui.  If a `str` is provided to `call_button`, it will be used as the text of
the button.

### `layout`

The `layout` option determines which layout class from the backend will be used.
Currently, only Qt backends are supported and valid layout options include:
`horizontal`, `vertical`, `form`, or `grid`.

Layouts are a work in progress...

## argument-specific options

As a reminder, a widget will be created in the GUI for each argument in the signature of
the function being decorated by `magicgui`.  These individual gui elements can be
modified by providing an options `dict` to a keyword argument to the `magicgui` function
with the same name as the argument in the signature that you want to modify:

### `widget_type`

`magicgui` makes some reasonable default guesses about what type of GUI widget to use,
based on the type or type annotation of your argument, but you can override this, or
provide specific instructions for custom types, using the `widget_type` option, which
expects a widget class that can be instantiated.  For instance, to turn an `int` into
a Qt Slider with a range (using [qt-specific options](#qt-specific-options)):

```python
from qtpy.QtWidgets import QSlider

@magicgui(arg={'widget_type': QSlider, 'minimum': 10, 'maximum': 100})
def my_func(arg=5):
    ...
```

## Qt-specific options

If you are using Qt as a backend (currently the only supported backend), you can provide
***any*** string matching one of the `widget.set<ParameterName>` methods for the corresponding
QWidget (see, for example, <a href="https://doc.qt.io/qt-5/qwidget-members.html"
target="_blank">all of the members for QWidget</a>).  If a setter is detected, `magicgui`
will call it with the value provided in the `magicgui` argument-specific.

For example to change the width and font for a specific field:

!!! hint
    The first letter in the parameter name needn't be capitalized as long as the rest
    of the string matches a corresponding setter on the widget. In this example, both
    "`font`" and "`Font`" keywords would properly call `widget.setFont()`

```python
from qtpy.QtGui import QFont

@magicgui(name={"fixedWidth": 200, "font": QFont('Arial', 20)})
def my_function(name: str):
    if name:
        return f"Hello, {name}!"

gui = my_function.Gui(show=True)
```

As another example, you can disable interactivity on a widget as follows:

```python
# the widget for `arg3` will be disabled
@magicgui(arg3={"disabled": True})
def my_function(arg2: int, arg2: int, arg3: str):
    ...
```

??? tip "Tip: creating a `result` field"
    Disabling one of the arguments can be used to create a "result" widget.

    ```python
    @magicgui(greeting={"disabled": True}, call_button="Hi!")
    def my_function(name: str, greeting=""):
        if name:
            return f"Hello, {name}!"

    gui = my_function.Gui(show=True)
    gui.called.connect(lambda result: gui.set_widget("greeting", result))
    ```

    <img src="../img/disabled_field.png" width="400"/>

    Note: It's rather unconventional to put the "output" variable in a python function
    signature... but it works for this example.  If you'd prefer, you can always omit the
    parameter from the function signature, and
    `gui.set_widget(name, [value, [position]])` will create a new widget for you at the
    specified `position`.  Keyword arguments in the `@magicgui` decorator matching the
    name of the new widget will still be used (such as `"disabled": True` here):

    ```python
    @magicgui(greeting={"disabled": True}, call_button="Hi!")
    def my_function(name: str):
        if name:
            return f"Hello, {name}!"

    gui = my_function.Gui(show=True)
    gui.called.connect(lambda result: gui.set_widget("greeting", result, position=-1))
    ```
