from contextlib import contextmanager
from typing import Any, Callable, Optional, Sequence, TypeVar, Union, overload

from magicgui.application import Application, AppRef, use_app
from magicgui.events import EventEmitter
from magicgui.protocols import ContainerProtocol
from magicgui.signature import magic_signature
from magicgui.type_map import _type2callback
from magicgui.widgets import Container, LineEdit, PushButton

F = TypeVar("F", bound=Callable[..., Any])


@overload
def magicgui(function: F) -> "FunctionGui":
    ...


@overload
def magicgui(function=None, **k) -> Callable[[F], "FunctionGui"]:
    ...


def magicgui(
    function: Optional[F] = None,
    *,
    orientation: str = "horizontal",
    labels: bool = True,
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    result_widget: bool = False,
    parent: Any = None,
    ignore: Optional[Sequence[str]] = None,
    app: AppRef = None,
    **param_options: dict,
):
    """Create a FunctionGui class for ``function`` and add it as an attribute ``Gui``.

    Parameters
    ----------
    function : Callable, optional
        The function to decorate.  Optional to allow bare decorator with optional
        arguments. by default None
    orientation : str, optional
        The type of layout to use. Must be one of {'horizontal', 'vertical',
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

    def inner_func(func: Callable) -> FunctionGui:
        return FunctionGui(
            function=func,
            call_button=call_button,
            orientation=orientation,
            param_options=param_options,
            auto_call=auto_call,
            result_widget=result_widget,
            app=app,
        )

    if function is None:
        return inner_func
    else:
        return inner_func(function)


class FunctionGui(Container):
    """Wrapper for a container of widgets representing a callable object."""

    __magicgui_app__: Application
    _widget: ContainerProtocol

    def __init__(
        self,
        function: Callable,
        call_button: Union[bool, str] = False,
        orientation: str = "horizontal",
        app: AppRef = None,
        show: bool = False,
        auto_call: bool = False,
        result_widget: bool = False,
        param_options: Optional[dict] = None,
        name: str = None,
        **k,
    ):
        """Create a new FunctionGui instance."""
        # if isinstance(function, FunctionGui):
        #     # don't redecorate already-wrapped function
        #     return function
        extra = set(k) - set(["kind", "default", "annotation", "gui_only"])
        if extra:
            s = "s" if len(extra) > 1 else ""
            raise TypeError(f"FunctionGui got unexpected keyword argument{s}: {extra}")
        self.__magicgui_app__ = use_app(app)
        sig = magic_signature(function, gui_options=param_options)
        super().__init__(
            orientation=orientation,
            widgets=list(sig.widgets(app).values()),
            return_annotation=sig.return_annotation,
            name=name or function.__name__,
        )

        self.called = EventEmitter(self, type="called")
        self._result_name = ""
        self._function = function

        if call_button:
            text = call_button if isinstance(call_button, str) else "Run"
            self._call_button = PushButton(gui_only=True, text=text, name="call_button")
            if not auto_call:  # (otherwise it already get's called)
                self._call_button.changed.connect(lambda e: self.__call__())
            self.append(self._call_button)

        self._result_widget: Optional[LineEdit] = None
        if result_widget:
            self._result_widget = LineEdit(gui_only=True, name="result")
            self._result_widget.enabled = False
            self.append(self._result_widget)

        if auto_call:
            self.changed.connect(lambda e: self.__call__())

        if show:
            self.show()

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
        # ... change parameters in the gui ... or by setting:  gui.param = something
        """
        sig = self.to_signature()
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        value = self._function(*bound.args, **bound.kwargs)
        if self._result_widget is not None:
            self._result_widget.value = value

        return_type = self._return_annotation
        if return_type:
            for callback in _type2callback(return_type):
                callback(self, value, return_type)
        self.called(value=value)
        return value

    def __repr__(self) -> str:
        """Return string representation of instance."""
        fname = f"{self._function.__module__}.{self._function.__name__}"
        return f"<FunctionGui {fname}{self.to_signature()}>"

    def show(self, run=False):
        """Show the widget."""
        super().show()
        if run:
            self.__magicgui_app__.run()

    @contextmanager
    def shown(self):
        """Context manager to show the widget."""
        try:
            super().show()
            yield self.__magicgui_app__.__enter__()
        finally:
            self.__magicgui_app__.__exit__()

    @property
    def result_name(self) -> str:
        """Return a name that can be used for the result of this magicfunction."""
        return self._result_name or (self._function.__name__ + " result")

    @result_name.setter
    def result_name(self, value: str):
        """Set the result name of this MagicGui widget."""
        self._result_name = value

    def Gui(self):
        import warnings

        warnings.warn(
            "Creating a widget instance with `my_function.Gui()` is deprecated,\n"
            "the magicgui decorator now returns a widget instance directly, so you\n"
            "should simply use the function itself as a magicgui widget, or call\n"
            "`my_function.show() to run the application.\n"
            "In a future version, the `Gui` attribute will be removed.",
            FutureWarning,
        )
        return self
