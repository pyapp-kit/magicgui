# migration guide

## v0.3.0 migration guide

*October, 2021*

Version 0.3.0 of magicgui introduced some changes to the events and callbacks API.
See https://github.com/pyapp-kit/magicgui/pull/253 for details

### Callbacks now receive the value directly, instead of an `Event` object

magicgui 0.3.0 is now using [psygnal](https://github.com/tlambert03/psygnal)
as its event/callback handler.

Callbacks connected to `widget.changed` (and other event emitters) may now receive the
value(s) directly, instead of an event object:

```python title="👎 Old Method (< v0.3.0)"
@widget.changed.connect
def my_callback(event):
    # event was an `Event` object with a `value` attribute
    new_value = event.value
```

Existing code using callbacks with a single positional
argument will continue to receive a single Event object (and a
warning will be shown, until v0.4.0 where it will become an error).

To silence the warning and opt in to the new pattern of receiving
value directly, you can do one of two things:

1. type hint your single positional argument as *anything* other than `magicgui.events.Event`
2. provide a callback that takes no arguments

```python title="👍 New Method (>= v0.3.0)"
@widget.changed.connect
def my_callback(new_value: int):
    ...  # use new_value directly

# or, if you don't need to use new_value
@widget.changed.connect
def my_callback():
    # something that didn't need the value
    ...
```

### Event emitters take no keyword arguments

For the few packages who were manually emitting change events,
you should no longer provide the `value=` keyword when emitting.

```python title="👎 Old Method (< v0.3.0)"
widget.changed(value='whatever')
```

```python title="👍 New Method (>= v0.3.0)"
widget.changed.emit('whatever')
# OR (if you prefer the direct __call__ syntax)
widget.changed('whatever')
```

## v0.2.0 migration guide

*December, 2020*

Version 0.2.0 of magicgui was a complete rewrite that introduced a couple
breaking API changes

### `.Gui()` attribute removed

Before `v0.2.0`, the [`magicgui.magicgui`][magicgui.magicgui] decorator added a `Gui` attribute to
the decorated function that was to be called to instantiate a widget.  In `v0.2.0`
the object returned from the [`magicgui.magicgui`][magicgui.magicgui] decorator is already an
instantiated [`magicgui.widgets.Widget`][magicgui.widgets.Widget].

```python title="👎 Old Method (< v0.2.0)"
from magicgui import magicgui, event_loop

@magicgui
def function(x, y):
    ...

with event_loop():
    gui = function.Gui(show=True)
```

```python title="👍 New Method (>= v0.2.0)"
from magicgui import magicgui

@magicgui
def function(x, y):
    ...

function.show(run=True)
```


### New base widget type

Before `v0.2.0`, the `Gui()` object returned by the [`magicgui.magicgui`][magicgui.magicgui]
decorator was a `MagicGuiBase` widget class, which in turn was a *direct
subclass* of a backend widget, such as a
[`QtWidgets.QWidget`](https://doc.qt.io/qt-5/qwidget.html).  In `v0.2.0`, all
widgets derive from [`magicgui.widgets.Widget``][magicgui.widgets.Widget],
and the *backend* is available at `widget.native`.  If you are incorporating
magicgui widgets into a larger Qt-based GUI, please note that you will want
to use `widget.native` instead of `widget`

```python
from magicgui import magicgui, use_app

use_app('qt')

@magicgui
def function(x, y):
    ...
```

```python
>>> print(type(function))
<class 'magicgui.widgets.FunctionGui'>
>>> print(type(function.native))
<class 'PyQt5.QtWidgets.QWidget'>
```

### Starting the application

It is now easier to show a widget and start an application by calling
`widget.show(run=True)`. Calling `show(run=True)` will *immediately* block
execution of your script and show the widget.  If you wanted to (for instance)
show *multiple* widgets next to each other, then you would still want to use the
`event_loop` context manager:

```python
from magicgui import magicgui, event_loop

@magicgui
def function_a(x=1, y=3):
    ...

@magicgui
def function_b(z='asdf'):
    ...

with event_loop():
    function_a.show()
    function_b.show()
# both widgets will show (though b may be on top of a)
```

### Getting and setting values

To get or set the value of a widget programmatically, you no
longer set the corresponding widget attribute directly, but rather
use the `widget.value` attribute:

!!!danger "**Old Method 👎**"
    `gui.x` used to be a
    [descriptor](https://docs.python.org/3/glossary.html#term-descriptor) object
    to get/set the value, but the actual underlying widget was at `gui.x_widget`

    ```python
    gui = function.Gui()
    gui.x = 10
    ```

!!!tip "**New Method 👍**"
    now `function.x` IS the widget, and you set its value with
    `function.x.value`

    ```python
    function.x.value = 10
    ```

### Connecting callbacks to events

When binding callbacks to change events, you no longer connect to
`gui.<name>_changed`, you now connect to `function.<name>.changed`:

```python title="👎 Old Method (< v0.2.0)"
gui = function.Gui()
gui.x_changed.connect(my_callback)
```

```python title="👍 New Method (>= v0.2.0)"
function.x.changed.connect(my_callback)
```

### Renamed

- `Widget.refresh_choices` has been renamed to `Widget.reset_choices`.

- `@magicgui(result=True)` has been renamed to `@magicgui(result_widget=True)`
