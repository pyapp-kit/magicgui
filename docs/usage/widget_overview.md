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

# Widget Overview

All indiviual graphical elements in `magicgui` are "widgets", and all widgets
are instances of {class}`magicgui.widgets.Widget`.  Widgets may be created
directly:

```{code-cell} python
from magicgui.widgets import LineEdit

line_edit = LineEdit(value='hello!')
line_edit.show()
```

Some widgets (such as {class}`magicgui.widgets.Container`) are composite
widgets that comprise other widgets:

```{code-cell} python
from magicgui.widgets import LineEdit, SpinBox, Container

line_edit = LineEdit(value='hello!')
spin_box = SpinBox(value=400)
container = Container(widgets=[line_edit, spin_box])
container.show()
```

`magicgui` provides a way to automatically select a widget given a python value
or type annotation using {func}`magicgui.widgets.create_widget`. Here is an
example that yields the same result as the one above:

```{code-cell} python
from magicgui.widgets import create_widget

x = 'hello!'
y = 400
container = Container(widgets=[create_widget(i) for i in (x, y)])
container.show()
```

```{note}
Because there are often multiple "valid" widget types for a given python object,
you may sometimes wish to create widgets directly, or use the `widget_type` argument
in {func}`~magicgui.widgets.create_widget`
```

## The widget hierarchy

Many widgets present similar types of information in different ways.  `magicgui` tries
to maintain a consistent API among all types of widgets that are designed to represent
similar objects.  The general class of widget you are working with will determine the
properties and attributes it has.

```{note}
The "categories" shown below (such as [`ValueWidget`](#valuewidget) and [`RangedWidget`]
(#rangedwidget-valuewidget)) are not intended to be instantiated directly.  Instead, you
would directly create the widget type you wanted, such as `LineEdit` or `SpinBox`,
respectively.
```

### `Widget`

As mentioned above, all magicgui widgets derive from {class}`magicgui.widgets.Widget` and have the
following attributes (this list is not comprehensive, see
the {class}`magicgui.widgets.Widget` API):

```{list-table}
:header-rows: 1
:name: widget-table
:widths: 6 12 50

* - attribute
  - type
  - description
* - **name**
  - *str, optional*
  - The name or "ID" of this widget (such as a function parameter name to
    which this widget corresponds). by default `""`
* - **annotation**
  - *Any, optional*
  - A type annotation for the value represented by the widget, by default
    `None`
* - **label**
  - *str, optional*
  - A string to use for an associated Label widget (if this widget is being
    shown in a {class}`~magicgui.widgets.Container` widget, and
    `container.labels` is `True`). By default, `name` will be used. Note: `name`
    refers the name of the parameter, as might be used in a signature, whereas
    label is just the label for that widget in the GUI.
* - **tooltip**
  - *str, optional*
  - A tooltip to display when hovering over the widget.
* - **visible**
  - *bool, optional*
  - Whether the widget is visible, by default `True`.
```

### `ValueWidget`

In addition to the base [`Widget`](#widget) properties mentioned above, the
following `ValueWidgets` track some `value`:

```{eval-rst}

.. currentmodule:: magicgui.widgets

.. autosummary::
   :nosignatures:
   :toctree: _autosummary

   Label
   LineEdit
   LiteralEvalLineEdit
   TextEdit
   FileEdit
   RangeEdit
   SliceEdit
   DateTimeEdit
   DateEdit
   TimeEdit
```

```{list-table}
:header-rows: 1
:name: value-widget-table
:widths: 6 12 50

* - attribute
  - type
  - description
* - **value**
  - *Any*
  - The current value of the widget.
* - **changed**
  - *EventEmitter*
  - An {class}`magicgui.events.EventEmiter` that will emit an event when the `value`
    has changed.  Connect callbacks to the change event using
    `widget.changed.connect(callback)`
* - **bind**
  - *Any, optional*
  - A value or callback to bind this widget.  If bound, whenever `widget.value` is
    accessed, the value provided here will be returned.  The bound value can be a
    callable, in which case `bound_value(self)` will be returned (i.e. your callback
    must accept a single parameter, which is this widget instance.). see
    {meth}`ValueWidget.bind <magicgui.widgets._bases.value_widget.ValueWidget.bind>`
    for details.
```

Here is a demonstration of all these:

```{code-cell} python
from magicgui import widgets
import datetime

wdg_list = [
    widgets.Label(value="label value", label="Label:"),
    widgets.LineEdit(value="line edit value", label="LineEdit:"),
    widgets.TextEdit(value="text edit value...", label="TextEdit:"),
    widgets.FileEdit(value="/home", label="FileEdit:"),
    widgets.RangeEdit(value=range(0, 10, 2), label="RangeEdit:"),
    widgets.SliceEdit(value=slice(0, 10, 2), label="SliceEdit:"),
    widgets.DateTimeEdit(
      value=datetime.datetime(1999, 12, 31, 11, 30), label="DateTimeEdit:"
    ),
    widgets.DateEdit(value=datetime.date(81, 2, 18), label="DateEdit:"),
    widgets.TimeEdit(value=datetime.time(12, 20), label="TimeEdit:"),
]
container = widgets.Container(widgets=wdg_list)
container.max_height = 300
container.show()
```

#### `RangedWidget(ValueWidget)`

`RangedWidgets` are numerical [`ValueWidgets`](#valuewidget) that have a restricted range of valid
values, and a step size.  `RangedWidgets` include:

```{eval-rst}

.. currentmodule:: magicgui.widgets

.. autosummary::
   :nosignatures:
   :toctree: _autosummary

   SpinBox
   FloatSpinBox
```

Ranged widgets attributes include:

```{list-table}
:header-rows: 1
:name: ranged-widget-table
:widths: 6 16 70

* - attribute
  - type
  - description
* - **min**
  - *float*
  - The minimum allowable value, by default 0
* - **min**
  - *float*
  - The maximum allowable value, by default 1000
* - **step**
  - *float*
  - The step size for incrementing the value, by default 1
* - **range**
  - *tuple of float*
  - A convenience attribute for getting/setting the (min, max) simultaneously

```

```{code-cell} python
w1 = widgets.SpinBox(value=10, max=20, label='SpinBox:')
w2 = widgets.FloatSpinBox(value=10.5, step=0.5, label='FloatSpinBox:')
container = widgets.Container(widgets=[w1, w2])
container.show()
```

##### `SliderWidget(RangedWidget)`

`SliderWidgets` are special [`RangedWidgets`](#rangedwidget-valuewidget)
that additionally have an `orientation`, and a `readout`.

```{eval-rst}

.. currentmodule:: magicgui.widgets

.. autosummary::
   :nosignatures:
   :toctree: _autosummary

   Slider
   FloatSlider
   LogSlider
   ProgressBar
```

```{list-table}
:header-rows: 1
:name: slider-widget-table
:widths: 6 12 50

* - attribute
  - type
  - description
* - **orientation**
  - *str, optional*
  - The orientation for the slider. Must be either `'horizontal'` or `'vertical'`.
    by default `'horizontal'`
* - **readout**
  - *bool, optional*
  - Whether to show the value of the slider. By default, `True`.
```

```{code-cell} python
w1 = widgets.Slider(value=10, max=25, label='Slider:')
w2 = widgets.FloatSlider(value=10.5, max=18.5, label='FloatSlider:')
w3 = widgets.ProgressBar(value=80, max=100, label='ProgressBar:')
container = widgets.Container(widgets=[w1, w2, w3])
container.show()
```

#### `ButtonWidget(ValueWidget)`

`ButtonWidgets` are boolean [`ValueWidgets`](#valuewidget) that also have some
`text` associated with them.

```{eval-rst}

.. currentmodule:: magicgui.widgets

.. autosummary::
   :nosignatures:
   :toctree: _autosummary

   PushButton
   CheckBox
```

```{list-table}
:header-rows: 1
:name: button-widget-table
:widths: 6 12 50

* - attribute
  - type
  - description
* - **text**
  - *str*
  - The text to display on the button. If not provided, will use ``name``.
```

```{code-cell} python
w1 = widgets.PushButton(value=True, text='PushButton.text')
w2 = widgets.CheckBox(value=False, text='CheckBox.text')
container = widgets.Container(widgets=[w1, w2])
container.show()
```

#### `CategoricalWidget(ValueWidget)`

`CategoricalWidget` are [`ValueWidgets`](#valuewidget) that provide a set
of valid choices.  They can be created from:

- an {class}`enum.Enum`
- an iterable of objects (or an iterable of 2-tuples `(name, object)`)
- a callable that returns an {class}`enum.Enum` or an iterable

```{eval-rst}

.. currentmodule:: magicgui.widgets

.. autosummary::
   :nosignatures:
   :toctree: _autosummary

   ComboBox
   RadioButtons
   Select
```

```{list-table}
:header-rows: 1
:name: categorical-widget-table
:widths: 6 12 50

* - attribute
  - type
  - description
* - **choices**
  - *Enum, Iterable, or Callable*
  - Available choices displayed in the widget.
* - **value**
  - *Any*
  - In the case of a `CategoricalWidget` the `value` is the *data* of the currently
    selected choice (see also: `current_choice` below).
* - **current_choice**
  - *str**
  - The name associated with the current choice.  For instance, if `choices` was provided
    as `choices=[('one', 1), ('two', 2)]`, then an example `value` would be `1`, and
    an example `current_choice` would be `'one'`.
```

```{code-cell} python
choices = ['one', 'two', 'three']
w1 = widgets.ComboBox(choices=choices, value='two', label='ComboBox:')
w2 = widgets.RadioButtons(choices=choices, label='RadioButtons:')
w3 = widgets.Select(choices=choices, label='Select:')
container = widgets.Container(widgets=[w1, w2, w3])
container.max_height = 220
container.show()
```

### `ContainerWidget`

A `ContainerWidget` is a list-like `Widget` that can contain other widgets.
Containers allow you to build more complex widgets from sub-widgets. A
notable example of a `Container` is {class}`magicgui.widgets.FunctionGui`)
(the product of the {func}`@magicgui <magicgui.magicgui>` decorator).

```{eval-rst}
.. currentmodule:: magicgui.widgets

.. autosummary::
   :nosignatures:
   :toctree: _autosummary

   Container
   MainWindow
   FunctionGui
```

```{list-table}
:header-rows: 1
:name: container-widget-table
:widths: 6 12 50

* - attribute
  - type
  - description
* - **layout**
  - *str*
  - The layout for the container.  must be either `'horizontal'` or `'vertical'`.
    by default "vertical"
* - **widgets**
  - *sequence of widgets*
  - The widget that the container contains.
* - **labels**
  - *bool, optional**
  - Whether each widget should be shown with a corresponding `Label` widget to the
    left, by default `True`.  Note: the text for each widget defaults to
    `widget.name`, but can be overriden by setting `widget.label`.
```

## `@magicgui`

The {func}`@magicgui <magicgui.magicgui>` decorator is a just convenience
function that builds a special type of {class}`magicgui.widgets.Container`
widget (a {class}`magicgui.widgets.FunctionGui`), with a widget representing
each of the parameters in a decorated function.

```{code-cell} python
from magicgui import magicgui

@magicgui
def my_function(x='hello', y=400): ...

my_function.show()
```

In terms of simply building widgets, the following code performs a similar
task to {func}`@magicgui <magicgui.magicgui>`.  Note, however, that the
{class}`magicgui.widgets.FunctionGui` widget produced by {func}`@magicgui <magicgui.magicgui>` is actually a *callable* widget that behaves very much like the
original function, using the parameters from the GUI when calling the function.

```{code-cell} python
from inspect import signature

def my_function(x='hello', y=400):
  ...

params = signature(my_function).parameters.values()
container = Container(
    widgets=[create_widget(p.default, name=p.name) for p in params]
)
container.show()
```
