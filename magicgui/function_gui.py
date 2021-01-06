"""The FunctionGui class is a Container subclass designed to represent a function.

The core `magicgui` decorator returns an instance of a FunctionGui widget.
"""
from __future__ import annotations

import inspect
import warnings
from typing import Any, Callable, Dict, Optional, Sequence, TypeVar, Union, overload

from magicgui.application import AppRef
from magicgui.events import EventEmitter
from magicgui.signature import magic_signature
from magicgui.type_map import _type2callback
from magicgui.widgets import Container, LineEdit, PushButton
from magicgui.widgets._protocols import ContainerProtocol


class FunctionGui(Container):
    """Wrapper for a container of widgets representing a callable object.

    Parameters
    ----------
    function : Callable
        A callable to turn into a GUI
    call_button : bool or str, optional
        If True, create an additional button that calls the original function when
        clicked.  If a ``str``, set the button text. by default False
    layout : str, optional
        The type of layout to use. Must be one of {'horizontal', 'vertical'}.
        by default "horizontal".
    labels : bool, optional
        Whether labels are shown in the widget. by default True
    app : magicgui.Application or str, optional
        A backend to use, by default ``None`` (use the default backend.)
    show : bool, optional
        Whether to immediately show the widget, by default False
    auto_call : bool, optional
        If True, changing any parameter in either the GUI or the widget attributes
        will call the original function with the current settings. by default False
    result_widget : bool, optional
        Whether to display a LineEdit widget the output of the function when called,
        by default False
    gui_options : dict, optional
        A dict of name: widget_options dict for each parameter in the function.
        Will be passed to `magic_signature` by default ``None``
    name : str, optional
        A name to assign to the Container widget, by default `function.__name__`
    bind : dict, optional
        A mapping of parameter names to values. Values supplied here will be permanently
        bound to the corresponding parameters: their widgets will be hidden from the GUI
        and the value will be used for the corresponding parameter when calling the
        function.

    Raises
    ------
    TypeError
        If unexpected keyword arguments are provided
    """

    _widget: ContainerProtocol

    def __init__(
        self,
        function: Callable,
        call_button: Union[bool, str] = False,
        layout: str = "horizontal",
        labels=True,
        app: AppRef = None,
        show: bool = False,
        auto_call: bool = False,
        result_widget: bool = False,
        param_options: Optional[dict] = None,
        name: str = None,
        bind: Dict[str, Any] = None,
        **kwargs,
    ):
        bind = bind or dict()
        # consume extra Widget keywords
        extra = set(kwargs) - {"annotation", "gui_only"}
        if extra:
            s = "s" if len(extra) > 1 else ""
            raise TypeError(f"FunctionGui got unexpected keyword argument{s}: {extra}")
        self._function = function
        sig = magic_signature(function, gui_options=param_options)
        super().__init__(
            layout=layout,
            labels=labels,
            widgets=list(sig.widgets(app).values()),
            return_annotation=sig.return_annotation,
            name=name or function.__name__,
        )

        self._param_options = param_options
        self.called = EventEmitter(self, type="called")
        self._result_name = ""
        self._bound: Dict[str, Any] = {}
        self.bind(bind)
        self._call_count: int = 0

        self._call_button: Optional[PushButton] = None
        if call_button:
            text = call_button if isinstance(call_button, str) else "Run"
            self._call_button = PushButton(gui_only=True, text=text, name="call_button")
            if not auto_call:  # (otherwise it already gets called)
                self._call_button.changed.connect(lambda e: self.__call__())
            self.append(self._call_button)

        self._result_widget: Optional[LineEdit] = None
        if result_widget:
            self._result_widget = LineEdit(gui_only=True, name="result")
            self._result_widget.enabled = False
            self.append(self._result_widget)

        self._auto_call = auto_call
        if auto_call:
            self.changed.connect(lambda e: self.__call__())

        if show:
            self.show()

    @property
    def call_count(self) -> int:
        """Return the number of times the function has been called."""
        return self._call_count

    def reset_call_count(self) -> None:
        """Reset the call count to 0."""
        self._call_count = 0

    def bind(self, kwargs: dict):
        """Bind key/value pairs to the function signature.

        Values supplied here will be permanently bound to the corresponding parameters:
        their widgets will be hidden from the GUI and the value will be used for the
        corresponding parameter when the function is called.

        Parameters
        ----------
        kwargs :  dict, optional
            A mapping of parameter names to values to bind.
        """
        self._bound.update(kwargs)
        for name, value in kwargs.items():
            getattr(self, name).hide()

    def unbind(self, args: Sequence):
        """Unbind keys from the function signature.

        Parameters
        ----------
        args : sequence
            A sequence of parameter names.  If any are currently bound to a value, the
            binding will be cleared and the widget will be shown.
        """
        for name in args:
            if name in self._bound:
                del self._bound[name]
                getattr(self, name).show()

    def __getattr__(self, value):
        """Catch deprecated _name_changed attribute."""
        if value.endswith("_changed"):
            widget_name = value.replace("_changed", "")
            warnings.warn(
                "\nThe `<name>_changed` signal has been removed in magicgui 0.2.0.\n"
                f"Use 'widget.{widget_name}.changed' instead of 'widget.{value}'",
                FutureWarning,
            )
            return getattr(self, widget_name).changed
        return super().__getattr__(value)

    # def __delitem__(self, key: Union[int, slice]):
    #     """Delete a widget by integer or slice index."""
    #     raise AttributeError("can't delete items from a FunctionGui")

    @property
    def __signature__(self):
        """Return an inspect.Signature subclass.

        The sig represents the original wrapped function, but with defaults and types
        from the widget (if different).
        """
        # FIXME: if someone has manually deleted widgets from the container, it may go
        # out of sync with the function signature.  Should prevent that.
        return self.to_signature()

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
        gui = FunctionGui(func, show=True)

        # then change parameters in the gui, or by setting:  gui.param.value = something

        gui()  # calls the original function with the current parameters
        """
        sig = self.to_signature()
        _kwargs = self._bound.copy()
        _kwargs.update(kwargs)
        bound = sig.bind(*args, **_kwargs)
        bound.apply_defaults()

        value = self._function(*bound.args, **bound.kwargs)
        self._call_count += 1
        if self._result_widget is not None:
            with self._result_widget.changed.blocker():
                self._result_widget.value = value

        return_type = self.return_annotation
        if return_type:
            for callback in _type2callback(return_type):
                callback(self, value, return_type)
        self.called(value=value)
        return value

    def __repr__(self) -> str:
        """Return string representation of instance."""
        fname = f"{self._function.__module__}.{self._function.__name__}"
        return f"<FunctionGui {fname}{self.to_signature()}>"

    @property
    def result_name(self) -> str:
        """Return a name that can be used for the result of this magicfunction."""
        return self._result_name or (self._function.__name__ + " result")

    @result_name.setter
    def result_name(self, value: str):
        """Set the result name of this FunctionGui widget."""
        self._result_name = value

    def copy(self, bind=None):
        """Return a copy of this FunctionGui, with optionally bound arguments."""
        return FunctionGui(
            function=self._function,
            call_button=bool(self._call_button),
            layout=self.layout,
            labels=self.labels,
            param_options=self._param_options,
            auto_call=self._auto_call,
            result_widget=bool(self._result_widget),
            app=None,
            bind=bind if bind is not None else self._bound,
        )

    # Cache function guis bound to specific instances
    _instance_guis: Dict[int, FunctionGui] = {}

    def __get__(self, obj, objtype=None) -> FunctionGui:
        """Provide descriptor protocol.

        This allows the @magicgui decorator to work on a function as well as a method.
        If a method on a class is decorated with `@magicgui`, then accessing the
        attribute on an instance of that class will return a version of the FunctionGui
        in which the first argument of the function is bound to the instance. (Just like
        what you'd expect with the @property decorator.)

        Example
        -------
        >>> class MyClass:
        ...     @magicgui
        ...     def my_method(self, x=1):
        ...         print(locals())
        ...
        >>> c = MyClass()
        >>> c.my_method  # the FunctionGui that can be used as a widget
        >>> c.my_method(x=34)  # calling it works as usual, with `c` provided as `self`
        {'self': <__main__.MyClass object at 0x7fb610e455e0>, 'x': 34}
        """
        if obj is not None:
            if id(obj) not in self._instance_guis:
                method = getattr(obj.__class__, self._function.__name__)
                params_names = list(inspect.signature(method).parameters)
                self._instance_guis[id(obj)] = self.copy(bind={params_names[0]: obj})
            return self._instance_guis[id(obj)]
        return self

    def __set__(self, obj, value):
        """Prevent setting a magicgui attribute."""
        raise AttributeError("Can't set magicgui attribute")

    def Gui(self, show=False):
        """Create a widget instance [DEPRECATED]."""
        warnings.warn(
            "\n\nCreating a widget instance with `my_function.Gui()` is deprecated,\n"
            "the magicgui decorator now returns a widget instance directly, so you\n"
            "should simply use the function itself as a magicgui widget, or call\n"
            "`my_function.show(run=True)` to run the application.\n"
            "In a future version, the `Gui` attribute will be removed.\n",
            FutureWarning,
        )
        if show:
            self.show()
        return self


# ==================   magicgui decorator   ===================================

F = TypeVar("F", bound=Callable[..., Any])


@overload
def magicgui(function: F, **k) -> FunctionGui:  # noqa: D103
    ...


@overload
def magicgui(function=None, **k) -> Callable[[F], FunctionGui]:  # noqa: D103
    ...


def magicgui(
    function: Optional[F] = None,
    *,
    layout: str = "horizontal",
    labels: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    app: AppRef = None,
    bind: Dict[str, Any] = None,
    **param_options: dict,
):
    """Return a :class:`FunctionGui` for ``function``.

    Parameters
    ----------
    function : Callable, optional
        The function to decorate.  Optional to allow bare decorator with optional
        arguments. by default ``None``
    layout : str, optional
        The type of layout to use. Must be one of {'horizontal', 'vertical'}.
        by default "horizontal".
    labels : bool, optional
        Whether labels are shown in the widget. by default True
    call_button : bool or str, optional
        If ``True``, create an additional button that calls the original function when
        clicked.  If a ``str``, set the button text. by default False
    auto_call : bool, optional
        If ``True``, changing any parameter in either the GUI or the widget attributes
        will call the original function with the current settings. by default False
    result_widget : bool, optional
        Whether to display a LineEdit widget the output of the function when called,
        by default False
    app : magicgui.Application or str, optional
        A backend to use, by default ``None`` (use the default backend.)
    bind : dict, optional
        A mapping of parameter names to values. Values supplied here will be permanently
        bound to the corresponding parameters: their widgets will be hidden from the GUI
        and the value will be used for the corresponding parameter when calling the
        function.

    **param_options : dict of dict
        Any additional keyword arguments will be used as parameter-specific options.
        Keywords MUST match the name of one of the arguments in the function
        signature, and the value MUST be a dict.

    Returns
    -------
    result : FunctionGui or Callable[[F], FunctionGui]
        If ``function`` is not ``None`` (such as when this is used as a bare decorator),
        returns a FunctionGui instance, which is a list-like container of autogenerated
        widgets corresponding to each parameter in the function.
        If ``function`` is ``None`` such as when arguments are provided like
        ``magicgui(auto_call=True)``, then returns a function that can be used as a
        decorator.

    Examples
    --------
    >>> @magicgui
    ... def my_function(a: int = 1, b: str = 'hello'):
    ...     pass
    ...
    >>> my_function.show()
    >>> my_function.a.value == 1  # True
    >>> my_function.b.value = 'world'
    """
    if "result" in param_options:
        warnings.warn(
            "\n\nThe 'result' option is deprecated and will be removed in the future."
            "Please use `result_widget=True` instead.\n",
            FutureWarning,
        )

        param_options.pop("result")
        result_widget = True

    def inner_func(func: Callable) -> FunctionGui:
        func_gui = FunctionGui(
            function=func,
            call_button=call_button,
            layout=layout,
            labels=labels,
            param_options=param_options,
            auto_call=auto_call,
            result_widget=result_widget,
            app=app,
            bind=bind,
        )
        func_gui.__wrapped__ = func
        return func_gui

    if function is None:
        return inner_func
    else:
        return inner_func(function)
