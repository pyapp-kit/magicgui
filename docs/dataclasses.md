# Dataclasses & guiclass

## What are dataclasses?

[`dataclasses`](https://docs.python.org/3/library/dataclasses.html) are a
feature added in Python 3.7
([PEP 557](https://www.python.org/dev/peps/pep-0557/)) that allow you to simply
define classes that store a specific set of data.  They encourage clear,
type-annotated code, and are a great way to define data structures with minimal
boilerplate.

!!!info "New to dataclasses?"

    If you're totally new to dataclasses, you might want to start with the
    [official documentation](https://docs.python.org/3/library/dataclasses.html)
    for the `dataclasses` module, or
    [this Real Python post on dataclasses](https://realpython.com/python-data-classes/).
    The following is a very brief example of the key features:

    ``` python title="Example dataclass"
    from dataclasses import dataclass

    @dataclass  # (1)!
    class Person:
        name: str # (2)!
        age: int = 0  # (3)!

    p = Person(name='John', age=30)  # (4)!
    print(p) # (5)!
    ```

    1. The `@dataclass` decorator is used to mark a class as a dataclass.  This
        will automatically generate an `__init__` method with a parameter for
        each annotated class attribute.
    2. Attribute names are annotated with types.  Note that, as with all Python
        type hints, these have no runtime effect (i.e. no validation is performed).
    3. Optional attributes can be defined with a default value. If no default value
        is specified, then the field is required when creating a new object.
    4. Creating a new object is as simple as passing in the required arguments.
    5. The `__repr__` method is automatically generated and will print out the
        class name and all of the attributes and their current values.

### dataclass patterns outside the standard library

The `dataclasses` module is not the only way to define data-focused classes in Python.
There are other libraries that provide similar functionality, and
some of them have additional features that are not available in the standard
library.

- [`attrs`](https://www.attrs.org/en/stable/) is a popular library that
  provides a number of additional features on top of the standard library
  `dataclasses`, including complex validation and type conversions.
- [`pydantic`](https://pydantic-docs.helpmanual.io/) is a library that provides
  runtime type enforcement and casting, serialization, and other features.
- [`msgspec`](https://github.com/jcrist/msgspec) is a fast serialization library
  with a `msgspec.Struct` that is similar to a dataclass.

## magicgui `guiclass`

!!! warning "Experimental"

    This is an experimental feature.  The API may change in the future without
    deprecations or warnings.

**magicgui** supports the dataclass API as a way to define the interface for compound
widget, where each attribute of the dataclass is a separate widget.  The
[`magicgui.experimental.guiclass`][magicgui.experimental.guiclass] decorator can be used to mark a class
as a "GUI class".  A GUI class *is* a Python standard [`dataclass`][dataclasses.dataclass]
that has two additional features:

1. A property (named "`gui`" by default) that returns a [`Container`][magicgui.widgets.Container]
   widget which contains a widget for each attribute of the dataclass.
2. An property (named "`events`" by default) that returns a
   [`psygnal.SignalGroup`][psygnal.SignalGroup] object that allows you to connect callbacks
   to the change event of any of field in the dataclass.  (Under the hood,
   this uses the
   [`@evented` dataclass decorator from `psygnal`](https://psygnal.readthedocs.io/en/latest/dataclasses/).)

!!! tip
    You can still use all of the standard dataclass features, including [`field`][dataclasses.field] values, [`__post_init__` processing](https://docs.python.org/3/library/dataclasses.html#post-init-processing), and [`ClassVar`](https://docs.python.org/3/library/dataclasses.html#class-variables).

!!! info
    In the future, we may also support other dataclass-like objects, such as
    [`pydantic` models](https://pydantic-docs.helpmanual.io/usage/models/),
    [`attrs` classes](https://www.attrs.org/en/stable/examples.html#classes),
    and [`traitlets` classes](https://traitlets.readthedocs.io/en/stable/api.html#traitlets.HasTraits).

``` python
from magicgui.experimental import guiclass

@guiclass
class MyDataclass:
    a: int = 0
    b: str = 'hello'
    c: bool = True

obj = MyDataclass()
obj.gui.show()
```

The individual widgets in the `Container` may be accessed by the same name as the
corresponding attribute. For example, `obj.gui.a` will return the `SpinBox` widget
that controls the value of the `a` attribute.

### Two-way data binding

As you interact programmatically with the `obj` instance, the widgets in the
`obj.gui` will update.  Similarly, as you change the value of the widgets in the
`obj.gui`, the values of the `obj` instance will be updated.

``` python
obj = MyDataclass(a=10)
obj.b = 'world'
obj.c = False

obj.gui.show()
```

!!! tip "All magicgui-related stuff is in the `gui` attribute"

    The original dataclass instance (`obj`) is essentially untouched.  Just as in a regular
    dataclass, `obj.a` returns the current value of `a` in the dataclass.  The *widget* for
    the class will be at `obj.gui` (or whatever name you specified in the `gui_name` parameter)
    So, `obj.gui.a.value`, returns the current value of the *widget*.  Unless you explicitly disconnect the gui from the underlying object/model, the two will always be in sync.

### Adding buttons and callbacks

Buttons are one of the few widget types that tend not to have an associated
value, but simply trigger a callback when clicked.  That is: it doesn't often
make sense to add a field to a dataclass representing a button. To add a button
to a `guiclass`, decorate a method with the [`magicgui.experimental.button`][magicgui.experimental.button]
decorator.

!!! warning "positioning buttons"
    Currently, all buttons are appended to the end of the widget. The ability
    to position the button in the layout will be added in the future.

Any additional keyword arguments to the `button` decorator will be passed to the
[`magicgui.widgets.PushButton`][magicgui.widgets.PushButton] constructor (e.g. `label`, `tooltip`, etc.)

``` python
from magicgui.experimental import guiclass, button

@guiclass
class Greeter:
    first_name: str

    @button
    def say_hello(self):
        print(f'Hello {self.first_name}')

greeter = Greeter('Talley')
greeter.gui.show()
```

> :point_up_2: *clicking the "say_hello" button will print "Hello Talley" to the console*

!!! tip

    As your widget begins to manage more internal state, the `guiclass` pattern
    becomes much more useful than the `magicgui` decorator pattern -- which was
    designed with pure functions that take inputs and return outputs in mind.
