# magicgui.magicgui

The `@magicgui` decorator is one of the main exports from `magicgui`. It
inspects the signature of a callable object, and selects a widget type
appropriate for each parameter in the signature.  It then returns a GUI (a
{class}`~magicgui.widgets.FunctionGui` instance to be precise) wrapping all of the widgets.  It can
be used to quickly generate an interactive graphical component that can control
and call the decorated function or method.

```{eval-rst}
.. autodecorator:: magicgui.magicgui
```
