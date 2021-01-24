"""The FunctionGui class is a Container subclass designed to represent a function.

The core `magicgui` decorator returns an instance of a FunctionGui widget.
"""
from __future__ import annotations

import inspect
import re
import warnings
from collections import deque
from contextlib import contextmanager
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Deque,
    Dict,
    Generic,
    Optional,
    TypeVar,
    Union,
)

from magicgui.application import AppRef
from magicgui.events import EventEmitter
from magicgui.signature import MagicSignature, magic_signature
from magicgui.widgets import Container, LineEdit, MainWindow, ProgressBar, PushButton
from magicgui.widgets._protocols import ContainerProtocol, MainWindowProtocol

if TYPE_CHECKING:
    from magicgui.widgets import TextEdit


def _inject_tooltips_from_docstrings(
    docstring: Optional[str], param_options: Dict[str, dict]
):
    """Update ``param_options`` dict with tooltips extracted from ``docstring``."""
    from docstring_parser import parse

    if not docstring:
        return

    doc_params = {p.arg_name: p.description for p in parse(docstring).params}

    # deal with the (numpydocs) case when there are multiple parameters separated
    # by a comma
    for k, v in list(doc_params.items()):
        if "," in k:
            for split_key in k.split(","):
                doc_params[split_key.strip()] = v
            del doc_params[k]

    for name, description in doc_params.items():
        # this is to catch potentially bad arg_name parsing in docstring_parser
        # if using napoleon style google docstringss
        argname = name.split(" ", maxsplit=1)[0]
        if argname not in param_options:
            param_options[argname] = {}
        desc = description.replace("`", "") if description else ""
        # use setdefault so as not to override an explicitly provided tooltip
        param_options[argname].setdefault("tooltip", desc)


_R = TypeVar("_R")


class FunctionGui(Container, Generic[_R]):
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
    tooltips : bool, optional
        Whether tooltips are shown when hovering over widgets. by default True
    app : magicgui.Application or str, optional
        A backend to use, by default ``None`` (use the default backend.)
    visible : bool, optional
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

    Raises
    ------
    TypeError
        If unexpected keyword arguments are provided
    """

    _widget: ContainerProtocol
    __signature__: MagicSignature

    def __init__(
        self,
        function: Callable[..., _R],
        call_button: Union[bool, str] = False,
        layout: str = "vertical",
        labels: bool = True,
        tooltips: bool = True,
        app: AppRef = None,
        visible: bool = False,
        auto_call: bool = False,
        result_widget: bool = False,
        param_options: Optional[Dict[str, dict]] = None,
        name: str = None,
        **kwargs,
    ):
        if not callable(function):
            raise TypeError("'function' argument to FunctionGui must be callable.")

        # consume extra Widget keywords
        extra = set(kwargs) - {"annotation", "gui_only"}
        if extra:
            s = "s" if len(extra) > 1 else ""
            raise TypeError(f"FunctionGui got unexpected keyword argument{s}: {extra}")
        if param_options is None:
            param_options = {}
        elif not isinstance(param_options, dict) or not all(
            isinstance(x, dict) for x in param_options.values()
        ):
            raise TypeError("'param_options' must be a dict of dicts")
        if tooltips:
            _inject_tooltips_from_docstrings(function.__doc__, param_options)

        self._function = function
        self.__wrapped__ = function
        # it's conceivable that function is not actually an instance of FunctionType
        # we can still support any generic callable, but we need to be careful not to
        # access attributes (like `__name__` that only function objects have).
        # Mypy doesn't seem catch this at this point:
        # https://github.com/python/mypy/issues/9934
        self._callable_name = (
            getattr(function, "__name__", None)
            or f"{function.__module__}.{function.__class__}"
        )

        sig = magic_signature(function, gui_options=param_options)
        super().__init__(
            layout=layout,
            labels=labels,
            visible=visible,
            widgets=list(sig.widgets(app).values()),
            return_annotation=sig.return_annotation,
            name=name or self._callable_name,
        )

        self._param_options = param_options
        self.called = EventEmitter(self, type="called")
        self._result_name = ""
        self._call_count: int = 0

        # a deque of Progressbars to be created by (possibly nested) tqdm_mgui iterators
        self._tqdm_pbars: Deque[ProgressBar] = deque()
        # the nesting level of tqdm_mgui iterators in a given __call__
        self._tqdm_depth: int = 0

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

    @property
    def call_count(self) -> int:
        """Return the number of times the function has been called."""
        return self._call_count

    def reset_call_count(self) -> None:
        """Reset the call count to 0."""
        self._call_count = 0

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

    def __call__(self, *args: Any, **kwargs: Any) -> _R:
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
        sig = self.__signature__
        try:
            bound = sig.bind(*args, **kwargs)
        except TypeError as e:
            if "missing a required argument" in str(e):
                match = re.search("argument: '(.+)'", str(e))
                missing = match.groups()[0] if match else "<param>"
                msg = (
                    f"{e} in call to '{self._callable_name}{sig}'.\n"
                    "To avoid this error, you can bind a value or callback to the "
                    f"parameter:\n\n    {self._callable_name}.{missing}.bind(value)"
                    "\n\nOr use the 'bind' option in the magicgui decorator:\n\n"
                    f"    @magicgui({missing}={{'bind': value}})\n"
                    f"    def {self._callable_name}{sig}: ..."
                )
                raise TypeError(msg) from None
            else:
                raise

        bound.apply_defaults()

        self._tqdm_depth = 0  # reset the tqdm stack count
        with _function_name_pointing_to_widget(self):
            value = self._function(*bound.args, **bound.kwargs)

        self._call_count += 1
        if self._result_widget is not None:
            with self._result_widget.changed.blocker():
                self._result_widget.value = value

        return_type = self.return_annotation
        if return_type:
            from magicgui.type_map import _type2callback

            for callback in _type2callback(return_type):
                callback(self, value, return_type)
        self.called(value=value)
        return value

    def __repr__(self) -> str:
        """Return string representation of instance."""
        return f"<{type(self).__name__} {self._callable_name}{self.__signature__}>"

    @property
    def result_name(self) -> str:
        """Return a name that can be used for the result of this magicfunction."""
        return self._result_name or (self._callable_name + " result")

    @result_name.setter
    def result_name(self, value: str):
        """Set the result name of this FunctionGui widget."""
        self._result_name = value

    def copy(self) -> FunctionGui:
        """Return a copy of this FunctionGui."""
        return FunctionGui(
            function=self._function,
            call_button=bool(self._call_button),
            layout=self.layout,
            labels=self.labels,
            param_options=self._param_options,
            auto_call=self._auto_call,
            result_widget=bool(self._result_widget),
            app=None,
        )

    _bound_instances: Dict[int, FunctionGui] = {}

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
            obj_id = id(obj)
            if obj_id not in self._bound_instances:
                method = getattr(obj.__class__, self._function.__name__)
                p0 = list(inspect.signature(method).parameters)[0]
                prior, self._param_options = self._param_options, {p0: {"bind": obj}}
                try:
                    self._bound_instances[obj_id] = self.copy()
                finally:
                    self._param_options = prior
            return self._bound_instances[obj_id]
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


class MainFunctionGui(FunctionGui[_R], MainWindow):
    """Container of widgets as a Main Application Window."""

    _widget: MainWindowProtocol

    def __init__(self, function: Callable, *args, **kwargs):
        super().__init__(function, *args, **kwargs)
        self.create_menu_item("Help", "Documentation", callback=self._show_docs)
        self._help_text_edit: Optional[TextEdit] = None

    def _show_docs(self):
        if not self._help_text_edit:
            from magicgui.widgets import TextEdit

            docs = self._function.__doc__
            html = _docstring_to_html(docs) if docs else "None"
            self._help_text_edit = TextEdit(value=html)
            self._help_text_edit.read_only = True
            self._help_text_edit.width = 600
            self._help_text_edit.height = 400

        self._help_text_edit.show()


def _docstring_to_html(docs: str) -> str:
    """Convert docstring into rich text html."""
    from docstring_parser import parse

    ds = parse(docs)

    ptemp = "<li><p><strong>{}</strong> (<em>{}</em>) - {}</p></li>"
    plist = [ptemp.format(p.arg_name, p.type_name, p.description) for p in ds.params]
    params = "<h3>Parameters</h3><ul>{}</ul>".format("".join(plist))
    short = f"<p>{ds.short_description}</p>" if ds.short_description else ""
    long = f"<p>{ds.long_description}</p>" if ds.long_description else ""
    return re.sub(r"``?([^`]+)``?", r"<code>\1</code>", f"{short}{long}{params}")


_UNSET = object()


@contextmanager
def _function_name_pointing_to_widget(function_gui: FunctionGui):
    """Context in which the name of the function points to the function_gui instance.

    When calling the function provided to FunctionGui, we make sure that the name
    of the function points to the FunctionGui object itself.
    In standard ``@magicgui`` usage, this will have been the case anyway.
    Doing this here allows the function name in a ``@magic_factory``-decorated function
    to *also* refer to the function gui instance created by the factory, (rather than
    to the :class:`~magicgui._magicgui.MagicFactory` object).

    Examples
    --------
    >>> @magicgui
    >>> def func():
    ...     # using "func" in the body here will refer to the widget.
    ...     print(type(func))
    >>>
    >>> func()  # prints 'magicgui.widgets._function_gui.FunctionGui'

    >>> @magic_factory
    >>> def func():
    ...     # using "func" in the body here will refer to the *widget* not the factory.
    ...     print(type(func))
    >>>
    >>> widget = func()
    >>> widget()  # *also* prints 'magicgui.widgets._function_gui.FunctionGui'
    """
    function = function_gui._function
    if not isinstance(function, FunctionType):
        # it's not a function object, so we don't know how to patch it...
        yield
        return

    func_name = function.__name__
    # see https://docs.python.org/3/library/inspect.html for details on code objects
    code = function.__code__

    if func_name in code.co_names:
        # This indicates that the function name was used inside the body of the
        # function, and points to some object in the module's global namespace.
        # function.__globals__ here points to the module-level globals in which the
        # function was defined.
        original_value = function.__globals__.get(func_name)
        function.__globals__[func_name] = function_gui
        try:
            yield
        finally:
            function.__globals__[func_name] = original_value

    elif function.__closure__ and func_name in code.co_freevars:
        # This indicates that the function name was used inside the body of the
        # function, and points to some object defined in a local scope (closure), rather
        # than the module's global namespace.
        # the position of the function name in code.co_freevars tells us where to look
        # for the value in the function.__closure__ tuple.
        idx = code.co_freevars.index(func_name)
        original_value = function.__closure__[idx].cell_contents
        function.__closure__[idx].cell_contents = function_gui
        try:
            yield
        finally:
            function.__closure__[idx].cell_contents = original_value
    else:
        yield
