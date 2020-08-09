import inspect
from functools import wraps
from typing import Any, Callable, Optional, Sequence, Union

from magicgui.application import use_app
from magicgui.container import Container
from magicgui.widget import Widget

import inspect


def magicgui(
    function: Optional[Callable] = None,
    layout: str = "horizontal",
    labels: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    parent: Any = None,
    ignore: Optional[Sequence[str]] = None,
    **param_options: dict,
) -> Callable:
    """Create a MagicGui class for ``function`` and add it as an attribute ``Gui``.

    Parameters
    ----------
    function : Callable, optional
        The function to decorate.  Optional to allow bare decorator with optional
        arguments. by default None
    layout : api.Layout or str, optional
        The type of layout to use.  If string, must be one of {'horizontal', 'vertical',
        'form', 'grid'}, by default "horizontal"
    labels : bool
        Whether labels are shown in the widget. by default True
    call_button : bool or str, optional
        If True, create an additional button that calls the original function when
        clicked.  If a ``str``, set the button text. by default False
    auto_call : bool, optional
        If True, changing any parameter in either the GUI or the widget attributes
        will call the original function with the current settings. by default False
    parent : api.WidgetType, optional
        An optional parent widget (note: this can be useful for inheriting styles),
        by default None
    ignore : list of str, optional
        Parameters in the function signature that should be ignored when creating
        the widget, by default None

    **param_options : dict of dict
        Any additional keyword arguments will be used as parameter-specific options.
        Keywords MUST match the name of one of the arguments in the function
        signature, and the value MUST be a dict.

    Returns
    -------
    Callable
        The original function is returned with a new attribute ``Gui``.  Gui is a
        subclass of MagicGui that, when instantiated, will create a widget representing
        the signature of the original function.  Furthermore, *calling* that widget will
        call the original function using the state of the Gui arguments.

    Examples
    --------
    >>> @magicgui
    ... def my_function(a: int = 1, b: str = 'hello'):
    ...     pass
    ...
    ... gui = my_function.Gui(show=True)
    """

    def inner_func(func: Callable) -> Callable:
        if param_options:
            valid = set(inspect.signature(func).parameters)
            invalid = set(param_options) - valid
            if invalid:
                raise ValueError(
                    "keyword arguments MUST match parameters in the decorated function."
                    f"\nExtra keys: {invalid}"
                )
            bad = {v for v in param_options.values() if not isinstance(v, dict)}
            if bad:
                s = "s" if len(bad) > 1 else ""
                raise TypeError(f"Value for parameter{s} {bad} must be a dict")

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            if hasattr(func, "_widget"):
                # a widget has been instantiated
                return getattr(func, "_widget")(*args, **kwargs)
            return func(*args, **kwargs)

        class MagicGui(MagicGuiBase):
            if hasattr(func, "__name__"):
                __doc__ = f'MagicGui generated for function "{func.__name__}"'

            def __init__(self, show: bool = False):
                super().__init__(
                    func,
                    layout=layout,
                    labels=labels,
                    call_button=call_button,
                    auto_call=auto_call,
                    parent=parent,
                    ignore=ignore,
                    **param_options,
                )
                setattr(wrapper, "called", self.called)
                if show:
                    self.show()

        setattr(wrapper, "Gui", MagicGui)
        return wrapper

    if function is None:
        return inner_func
    else:
        return inner_func(function)


class GuiFunction:
    def __init__(self, function, call_button: Union[bool, str] = False, app=None):
        app = use_app(app)
        self.widgets = Container.from_callable(function)
        self._function = function

        if call_button:
            self.call_button = Widget(options={"widget_type": "PushButton"})
            call_button if isinstance(call_button, str) else "call"
            # using lambda because the clicked signal returns a value
            self.call_button.value_changed.connect(lambda x: self.__call__())
            self.widgets.append(self.call_button)

    def __getattr__(self, name):
        if name != "widgets":
            try:
                return getattr(self.widgets, name)
            except AttributeError:
                pass
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if name != "widgets":
            widget = getattr(self.widgets, name, None)
            if widget:
                widget.value = value
                return
        super().__setattr__(name, value)

    def __call__(self, *args: Any, **kwargs: Any):
        """Call the original function with the current parameter values from the Gui.

        It is also possible to override the current parameter values from the GUI by
        providing args/kwargs to the function call.  Only those provided will override
        the ones from the gui.  A `called` signal will also be emitted with the results.

        Returns
        -------
        result : Any
            whatever the return value of the original function would have been.

        Examples
        --------
        gui = decorated_function.Gui(show=True)
        # ... change parameters in the gui ... or by setting:  gui.param = something

        # this will call the original function with the current parameters from the gui
        decorated_function()
        # this will override parameters from the gui with only the arg values specified
        decorated_function(arg='something')
        """
        # everything will be delivered as a keyword argument to self.func ...
        # get the current parameters from the gui

        sig = self.widgets.to_signature()
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        value = self._function(*bound.args, **bound.kwargs)
        # self.called.emit(value)

        return_type = self.widgets._return_annotation
        # if return_type:
        #     for callback in _type2callback(return_type):
        #         callback(self, value, return_type)
        return value

    def __repr__(self) -> str:
        fname = f"{self._function.__module__}.{self._function.__qualname__}"
        return f"<GuiFunction {fname}{self.widgets.to_signature()}>"

    def show(self):
        self.widgets.show()

    @property
    def __signature__(self) -> inspect.Signature:
        # this lets inspect.signature() still work on a wrapped function.
        return self.widgets.to_signature()
