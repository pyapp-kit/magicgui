"""The FunctionGui class is a Container subclass designed to represent a function.

The core `magicgui` decorator returns an instance of a FunctionGui widget.
"""
from __future__ import annotations

import inspect
import re
from collections import deque
from contextlib import contextmanager
from types import FunctionType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterator,
    NoReturn,
    TypeVar,
    cast,
)

from psygnal import Signal

from magicgui._type_resolution import resolve_single_type
from magicgui.signature import MagicSignature, magic_signature
from magicgui.widgets import Container, MainWindow, ProgressBar, PushButton
from magicgui.widgets.bases import ValueWidget

if TYPE_CHECKING:
    from pathlib import Path

    from typing_extensions import ParamSpec

    from magicgui.application import Application, AppRef  # noqa: F401
    from magicgui.widgets import TextEdit
    from magicgui.widgets.protocols import ContainerProtocol, MainWindowProtocol

    _P = ParamSpec("_P")
else:
    _P = TypeVar("_P")  # easier runtime dependency than ParamSpec


def _inject_tooltips_from_docstrings(
    docstring: str | None, sig: MagicSignature
) -> None:
    """Update `sig` gui options with tooltips extracted from `docstring`."""
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
        desc = description.replace("`", "") if description else ""
        # some docstring params may be mislabeled and not appear in the params
        if argname in sig.parameters:
            # use setdefault so as not to override an explicitly provided tooltip
            sig.parameters[argname].options.setdefault("tooltip", desc)


_R = TypeVar("_R")
_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class FunctionGui(Container, Generic[_P, _R]):
    """Wrapper for a container of widgets representing a callable object.

    Parameters
    ----------
    function : Callable
        A callable to turn into a GUI
    call_button : bool | str | None, optional
        If True, create an additional button that calls the original function when
        clicked.  If a `str`, set the button text. by default False when
        auto_call is True, and True otherwise.
        The button can be accessed from the `.call_button` property.
    layout : str, optional
        The type of layout to use. Must be `horizontal` or `vertical`
        by default "horizontal".
    scrollable : bool, optional
        Whether to enable scroll bars or not. If enabled, scroll bars will
        only appear along the layout direction, not in both directions.
    labels : bool, optional
        Whether labels are shown in the widget. by default True
    tooltips : bool, optional
        Whether tooltips are shown when hovering over widgets. by default True
    app : Application | str | None, optional
        A backend to use, by default `None` (use the default backend.)
    visible : bool, optional
        Whether to immediately show the widget.  If `False`, widget is explicitly
        hidden.  If `None`, widget is not shown, but will be shown if a parent
        container is shown, by default None.
    auto_call : bool, optional
        If True, changing any parameter in either the GUI or the widget attributes
        will call the original function with the current settings. by default False
    result_widget : bool, optional
        Whether to display a LineEdit widget the output of the function when called,
        by default False
    param_options : dict, optional
        A dict of name: widget_options dict for each parameter in the function.
        Will be passed to `magic_signature` by default `None`
    name : str, optional
        A name to assign to the Container widget, by default `function.__name__`
    persist : bool, optional
        If `True`, when parameter values change in the widget, they will be stored to
        disk (in `~/.config/magicgui/cache`) and restored when the widget is loaded
        again with `persist = True`.  By default, `False`.
    raise_on_unknown : bool
        If True, raise an error if a parameter annotation is not recognized.

    Raises
    ------
    TypeError
        If unexpected keyword arguments are provided
    """

    called = Signal(
        object, description="Emitted with the result after the function is called."
    )
    _widget: ContainerProtocol

    def __init__(
        self,
        function: Callable[_P, _R],
        call_button: bool | str | None = None,
        layout: str = "vertical",
        scrollable: bool = False,
        labels: bool = True,
        tooltips: bool = True,
        app: AppRef | None = None,
        visible: bool | None = None,
        auto_call: bool = False,
        result_widget: bool = False,
        param_options: dict[str, dict] | None = None,
        name: str | None = None,
        persist: bool = False,
        raise_on_unknown: bool = False,
        **kwargs: Any,
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
        elif not isinstance(param_options, dict):
            raise TypeError("'param_options' must be a dict of dicts")

        sig = magic_signature(
            function, gui_options=param_options, raise_on_unknown=raise_on_unknown
        )
        self._return_annotation = resolve_single_type(sig.return_annotation)
        self._tooltips = tooltips
        if tooltips:
            _inject_tooltips_from_docstrings(function.__doc__, sig)

        self.persist = persist
        self._function = function
        self.__wrapped__ = function
        # it's conceivable that function is not actually an instance of FunctionType
        # we can still support any generic callable, but we need to be careful not to
        # access attributes (like `__name__` that only function objects have).
        # Mypy doesn't seem catch this at this point:
        # https://github.com/python/mypy/issues/9934
        name = name or getattr(function, "__name__", None)
        if not name:
            if hasattr(function, "func"):  # partials:
                f = getattr(function, "func", None)
                name = getattr(f, "__name__", None) or str(function)
            else:
                name = f"{function.__module__}.{function.__class__}"
        self._callable_name = name

        super().__init__(
            layout=layout,
            scrollable=scrollable,
            labels=labels,
            visible=visible,
            widgets=list(sig.widgets(app).values()),
            name=name or self._callable_name,
        )
        self._param_options = param_options
        self._result_name = ""
        self._call_count: int = 0
        self._bound_instances: dict[int, FunctionGui] = {}

        # a deque of Progressbars to be created by (possibly nested) tqdm_mgui iterators
        self._tqdm_pbars: deque[ProgressBar] = deque()
        # the nesting level of tqdm_mgui iterators in a given __call__
        self._tqdm_depth: int = 0

        if call_button is None:
            call_button = not auto_call
        self._call_button: PushButton | None = None
        if call_button:
            text = call_button if isinstance(call_button, str) else "Run"
            self._call_button = PushButton(gui_only=True, text=text, name="call_button")
            if not auto_call:  # (otherwise it already gets called)

                @self._call_button.changed.connect
                def _disable_button_and_call() -> None:
                    # disable the call button until the function has finished
                    self._call_button = cast(PushButton, self._call_button)
                    self._call_button.enabled = False
                    try:
                        self.__call__()
                    finally:
                        self._call_button.enabled = True

            self.append(self._call_button)

        self._result_widget: ValueWidget | None = None
        if result_widget:
            from magicgui.widgets.bases import create_widget

            self._result_widget = cast(
                ValueWidget,
                create_widget(
                    value=None,
                    annotation=self._return_annotation,
                    gui_only=True,
                    is_result=True,
                    raise_on_unknown=raise_on_unknown,
                ),
            )
            self.append(self._result_widget)

        if persist:
            self._load(quiet=True)

        self._auto_call = auto_call
        self.changed.connect(self._on_change)

    def _on_change(self) -> None:
        if self.persist:
            self._dump()
        if self._auto_call:
            self()

    @property
    def call_button(self) -> PushButton | None:
        """Return the call button."""
        return self._call_button

    @property
    def call_count(self) -> int:
        """Return the number of times the function has been called."""
        return self._call_count

    def reset_call_count(self) -> None:
        """Reset the call count to 0."""
        self._call_count = 0

    @property
    def return_annotation(self) -> Any:
        """Return annotation for [inspect.Signature][inspect.Signature] conversion.

        ForwardRefs will be resolve when setting the annotation.
        """
        return self._return_annotation

    @property
    def __signature__(self) -> MagicSignature:
        """Return a MagicSignature object representing the current state of the gui."""
        return super().__signature__.replace(return_annotation=self.return_annotation)

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """Call the original function with the current parameter values from the Gui.

        You may pass a `update_widget=True` keyword argument to update the widget
        values to match the current parameter values before calling the function.

        It is also possible to override the current parameter values from the GUI by
        providing args/kwargs to the function call.  Only those provided will override
        the ones from the gui.  A `called` signal will also be emitted with the results.

        Returns
        -------
        result : Any
            whatever the return value of the original function would have been.

        Examples
        --------
        ```python
        gui = FunctionGui(func, show=True)

        # then change parameters in the gui, or by setting:  gui.param.value = something

        gui()  # calls the original function with the current parameters
        ```
        """
        update_widget: bool = bool(kwargs.pop("update_widget", False))

        sig = self.__signature__
        try:
            bound = sig.bind(*args, **kwargs)
        except TypeError as e:
            if "missing a required argument" not in str(e):
                raise

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

        if update_widget:
            self._auto_call, before = False, self._auto_call
            try:
                self.update(bound.arguments)
            finally:
                self._auto_call = before

        bound.apply_defaults()

        self._tqdm_depth = 0  # reset the tqdm stack count
        with _function_name_pointing_to_widget(self):
            value = self._function(*bound.args, **bound.kwargs)

        self._call_count += 1
        if self._result_widget is not None:
            with self._result_widget.changed.blocked():
                self._result_widget.value = value

        return_type = sig.return_annotation
        if return_type:
            from magicgui.type_map import type2callback

            for callback in type2callback(return_type):
                callback(self, value, return_type)
        self.called.emit(value)
        return value

    def __repr__(self) -> str:
        """Return string representation of instance."""
        return f"<{type(self).__name__} {self._callable_name}{self.__signature__}>"

    @property
    def result_name(self) -> str:
        """Return a name that can be used for the result of this magicfunction."""
        return self._result_name or f"{self._callable_name} result"

    @result_name.setter
    def result_name(self, value: str) -> None:
        """Set the result name of this FunctionGui widget."""
        self._result_name = value

    def copy(self) -> FunctionGui:
        """Return a copy of this FunctionGui."""
        return FunctionGui(
            function=self._function,
            call_button=self._call_button.text if self._call_button else None,
            layout=self.layout,
            labels=self.labels,
            param_options=self._param_options,
            auto_call=self._auto_call,
            result_widget=bool(self._result_widget),
            app=None,
            persist=self.persist,
            visible=self.visible,
            tooltips=self._tooltips,
            scrollable=self._scrollable,
            name=self.name,
        )

    def __get__(self, obj: object, objtype: type | None = None) -> FunctionGui:
        """Provide descriptor protocol.

        This allows the @magicgui decorator to work on a function as well as a method.
        If a method on a class is decorated with `@magicgui`, then accessing the
        attribute on an instance of that class will return a version of the FunctionGui
        in which the first argument of the function is bound to the instance. (Just like
        what you'd expect with the @property decorator.)

        Returns
        -------
        bound : FunctionGui
            A new FunctionGui instance.

        Examples
        --------
        ```python
        >>> class MyClass:
        ...     @magicgui
        ...     def my_method(self, x=1):
        ...         print(locals())
        ...
        >>> c = MyClass()
        >>> c.my_method  # the FunctionGui that can be used as a widget

        # calling it works as usual, with `c` provided as `self`
        >>> c.my_method(x=34)
        {'self': <__main__.MyClass object at 0x7fb610e455e0>, 'x': 34}
        ```
        """
        if obj is None:
            return self
        obj_id = id(obj)
        if obj_id not in self._bound_instances:
            method = getattr(obj.__class__, self._function.__name__)
            p0 = next(iter(inspect.signature(method).parameters))
            prior, self._param_options = self._param_options, {
                p0: {"bind": obj},
                **self._param_options,
            }
            try:
                self._bound_instances[obj_id] = self.copy()
            finally:
                self._param_options = prior
        return self._bound_instances[obj_id]

    def __set__(self, obj: Any, value: Any) -> NoReturn:
        """Prevent setting a magicgui attribute."""
        raise AttributeError("Can't set magicgui attribute")

    @property
    def _dump_path(self) -> Path:
        from magicgui._util import user_cache_dir

        name = getattr(self._function, "__qualname__", self._callable_name)
        name = name.replace("<", "-").replace(">", "-")  # e.g. <locals>
        return user_cache_dir() / f"{self._function.__module__}.{name}"

    def _dump(self, path: str | Path | None = None) -> None:
        super()._dump(path or self._dump_path)

    def _load(self, path: str | Path | None = None, quiet: bool = False) -> None:
        super()._load(path or self._dump_path, quiet=quiet)


class MainFunctionGui(FunctionGui[_P, _R], MainWindow):
    """Container of widgets as a Main Application Window."""

    _widget: MainWindowProtocol

    def __init__(self, function: Callable[_P, _R], *args: Any, **kwargs: Any) -> None:
        super().__init__(function, *args, **kwargs)
        self.create_menu_item("Help", "Documentation", callback=self._show_docs)
        self._help_text_edit: TextEdit | None = None

    def _show_docs(self) -> None:
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
    params = f'<h3>Parameters</h3><ul>{"".join(plist)}</ul>'
    short = f"<p>{ds.short_description}</p>" if ds.short_description else ""
    long = f"<p>{ds.long_description}</p>" if ds.long_description else ""
    return re.sub(r"`?([^`]+)`?", r"<code>\1</code>", f"{short}{long}{params}")


@contextmanager
def _function_name_pointing_to_widget(function_gui: FunctionGui) -> Iterator[None]:
    """Context in which the name of the function points to the function_gui instance.

    When calling the function provided to FunctionGui, we make sure that the name
    of the function points to the FunctionGui object itself.
    In standard `@magicgui` usage, this will have been the case anyway.
    Doing this here allows the function name in a `@magic_factory`-decorated function
    to *also* refer to the function gui instance created by the factory, (rather than
    to the [~magicgui._magicgui.MagicFactory][magicgui._magicgui.MagicFactory] object).

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
