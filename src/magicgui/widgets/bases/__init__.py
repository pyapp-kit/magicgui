"""Widget base classes.

These will rarely be used directly by end-users, instead see the "concrete" widgets
exported in :mod:`magicgui.widgets`.

All magicgui [Widget][magicgui.widgets.Widget] bases comprise a backend widget that
implements one of the widget protocols defined in
[`magicgui.widgets.protocols`](protocols). The basic composition pattern is as follows:

.. code-block:: python

   class Widget:

       def __init__(
            self,

            # widget_type is a class, likely from the `backends` module
            # that implements one of the `WidgetProtocols` defined in _protocols.
            widget_type: Type[protocols.WidgetProtocol],

            # backend_kwargs is a key-value map of arguments that will be provided
            # to the concrete (backend) implementation of the WidgetProtocol
            backend_kwargs: dict = dict(),

            # additional kwargs will be provided to the magicgui.Widget itself
            # things like, `name`, `value`, etc...
            **kwargs
        ):
           # instantiation of the backend widget.
           self._widget = widget_type(**backend_kwargs)

           # ... go on to set other kwargs


These widgets are unlikely to be instantiated directly, (unless you're creating a custom
widget that implements one of the WidgetProtocols... as the backed widgets do).
Instead, one will usually instantiate the widgets in :mod:`magicgui.widgets._concrete`
which are all available directly in the :mod:`magicgui.widgets` namespace.

The :func:`~magicgui.widgets.create_widget` factory function may be used to
create a widget subclass appropriate for the arguments passed (such as "value" or
"annotation").

"""

from ._button_widget import ButtonWidget
from ._categorical_widget import CategoricalWidget
from ._container_widget import ContainerWidget, DialogWidget, MainWindowWidget
from ._create_widget import create_widget
from ._ranged_widget import RangedWidget, TransformedRangedWidget
from ._slider_widget import MultiValuedSliderWidget, SliderWidget
from ._toolbar import ToolBarWidget
from ._value_widget import ValueWidget
from ._widget import Widget

__all__ = [
    "ButtonWidget",
    "CategoricalWidget",
    "ContainerWidget",
    "create_widget",
    "DialogWidget",
    "MainWindowWidget",
    "MultiValuedSliderWidget",
    "RangedWidget",
    "SliderWidget",
    "ToolBarWidget",
    "TransformedRangedWidget",
    "ValueWidget",
    "Widget",
]
