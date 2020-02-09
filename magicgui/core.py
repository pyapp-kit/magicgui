import functools
import inspect
from enum import Enum
from typing import Any, Callable, Iterable, Optional, Sequence, Type, Union

from qtpy.QtWidgets import QHBoxLayout

from . import _qt as api

# ######### decorator ######### #


def magicgui(
    function: Callable = None,
    layout: Union[api.Layout, str] = "horizontal",
    call_button: Union[bool, str] = False,
    parent: api.WidgetType = None,
    **kwargs: dict,
) -> Callable:
    """a decorator

    Parameters
    ----------
    function : Callable, optional
        [description], by default None
    layout : Union[api.Layout, str], optional
        [description], by default "horizontal"
    call_button : bool, optional
        [description], by default False

    Returns
    -------
    Callable
        The original function is returned with a new attribute Gui.  Gui is a subclass
        of MagicGui that, when instantiated, will create a widget representing the
        signature of the original function.  Furthermore, *calling* that widget will
        call the original function using the state of the Gui arguments.

    Examples
    --------


    """
    _layout = api.Layout[layout] if isinstance(layout, str) else layout

    def inner_func(func: Callable) -> Type:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if hasattr(func, "widget"):
                # a widget has been instantiated
                return func.widget(*args, **kwargs)
            return func(*args, **kwargs)

        class MagicGui(MagicGuiBase):
            __doc__ = f'MagicGui generated for function "{func.__name__}"'

            def __init__(self, show=False) -> None:
                super().__init__(
                    func, layout=_layout, call_button=call_button, **kwargs
                )
                wrapper.called = self.called
                if show:
                    self.show()

        wrapper.Gui = MagicGui
        return wrapper

    return inner_func if function is None else inner_func(function)


# ######### Base MagicGui Class ######### #


class MagicGuiBase(api.WidgetType):

    called = api.Signal(object)
    _widget_attr = "{}_widget"

    def __init__(
        self,
        func: Callable,
        *,
        layout=QHBoxLayout,
        call_button=False,
        parent=None,
        **kwargs: dict,
    ) -> None:
        self.params = inspect.signature(func).parameters
        self.param_names = tuple(self.params)
        super().__init__(parent=parent)
        self.func = func
        setattr(func, "widget", self)
        self.setLayout(layout.value(self))
        self.arg_options = kwargs
        for param in self.params.values():
            self.set_widget(
                name=param.name,
                value=(None if param.default is param.empty else param.default),
                dtype=(None if param.annotation is param.empty else param.annotation),
                **self.arg_options.get(param.name, {}),
            )

        if call_button:
            self.call_button = api.ButtonType(
                call_button if isinstance(call_button, str) else "call"
            )
            self.call_button.clicked.connect(self.__call__)
            self.layout().addWidget(self.call_button)

    def set_widget(
        self,
        name: str,
        value: Any = None,
        dtype: Optional[Type] = None,
        choices: Optional[Sequence[str]] = None,
    ) -> api.WidgetType:
        """Make a widget named `name` based on the type of signature param.

        A descriptor will also be added as an attribute to this class (named `name`).
        The descriptor provides the __get__ and __set__ methods that enable updating the
        GUI by simply setting the attribute on the MagicGui instance that has the same
        name as the argument in the function signature.

        Parameters
        ----------
        name : str
            the name of the argument in the function signature
        param : inspect.Parameter
            a parameter instance
        choices : Optional[Sequence[str]]
            If provided, typing for this widget will be overridden and it will become a
            dropdown menu type (e.g. QComboBox for Qt), and `choices` will be added as
            items in the menu.

        Raises
        ------
        ValueError
            if the 'choices' option was specified for this argument, but the default
            value was not one of the choices
        """

        # TODO: move choices logic out of this method
        if choices:
            if (value is not None) and (value not in choices):
                raise ValueError(
                    '"choices" option was provided, but the default value '
                    f"({value}) was not in the provided choices "
                    f"{choices}"
                )
            arg_type = Enum
        elif dtype is not None:
            arg_type = dtype
        elif value is not None:
            arg_type = type(value)
        else:
            arg_type = type(None)
        WidgetType = type2widget(arg_type)

        position = None
        existing_widget = getattr(self, self._widget_attr.format(name), None)
        # if there is already a widget by this name...
        if existing_widget:
            # if it has the same widget type as the new one, update the value
            if isinstance(existing_widget, WidgetType):
                setattr(self, name, value)
                return
            # otherwise delete it, but get the position so we can insert the new one.
            else:
                position = self.layout().indexOf(existing_widget)
                delattr(self, name)

        widget = WidgetType(parent=self)  # XXX: parent is Qt-specific
        self._decorate_widget(name, widget)
        if choices or issubclass(arg_type, Enum):
            self.set_choices(name, choices or arg_type)

        # self.add_widget_descriptor(name, widget)
        if value is not None:
            setattr(self, name, value)
        if position is not None:
            self.layout().insertWidget(position, widget)
        else:
            self.layout().addWidget(widget)

        return widget

    def _decorate_widget(self, name: str, widget: api.WidgetType) -> None:
        # puts api-agnostic getters/setters on the widget
        setattr(self, self._widget_attr.format(name), widget)
        getter, setter, onchange = api.getter_setter_onchange(widget)
        widget._get = getter
        widget._set = setter
        setattr(self, "_on_" + name, onchange)

    def __getattr__(self, name) -> Any:
        if name != "param_names" and name in self.param_names:
            return getattr(self, self._widget_attr.format(name))._get()
        return super().__getattr__(name)

    def __setattr__(self, name, val) -> None:
        if hasattr(self, "param_names") and name in self.param_names:
            widget = getattr(self, self._widget_attr.format(name))
            if api.is_categorical(widget):
                val = api.get_categorical_index(widget, val)
            return getattr(self, self._widget_attr.format(name))._set(val)
        object.__setattr__(self, name, val)

    def __delattr__(self, name: str) -> None:
        if name in self.param_names:
            widget = getattr(self, self._widget_attr.format(name))
            self.layout().removeWidget(widget)
            widget.deleteLater()
        super().__delattr__(name)

    def set_choices(self, name, choices: Union[Type[Enum], Iterable[Any]]) -> None:
        widget = getattr(self, self._widget_attr.format(name), None)
        if not widget:
            raise AttributeError(f"'{self}' object has no widget named '{name}'")
        if not api.is_categorical(widget):
            raise TypeError(f"'{name}' is not a categorical widget with choices.")
        if inspect.isclass(choices) and issubclass(choices, Enum):
            api.set_categorical_choices(widget, [(x.name, x) for x in choices])
        else:
            api.set_categorical_choices(widget, [(str(c), c) for c in choices])

    @property
    def current_kwargs(self) -> dict:
        return {param.name: getattr(self, param.name) for param in self.params.values()}

    def __call__(self, *args, **kwargs) -> Any:
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
        _kwargs = self.current_kwargs
        # update them with any positional args from the function call
        _kwargs.update({self.param_names[n]: arg for n, arg in enumerate(args)})
        # then update them with any keyword argumnets from the function call
        _kwargs.update(kwargs)
        # finally, call the original function, emit the result as a signal, and return.
        value = self.func(**_kwargs)
        self.called.emit(value)
        return value

    def __repr__(self):
        sig_string = ", ".join([f"{n}={k}" for n, k in self.current_kwargs.items()])
        func_string = f"{self.func.__name__}({sig_string})"
        return f"<MagicGui: {func_string}>"


# ######### UTIL FUNCTIONS ######### #


def type2widget(type_: type) -> Type[api.WidgetType]:
    WidgetType = api.type2widget(type_)
    if not WidgetType:
        raise TypeError(f'Unable to convert type "{type_}" into a widget.')
    return WidgetType
