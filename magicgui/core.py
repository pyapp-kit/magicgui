import functools
import inspect
import warnings
from enum import EnumMeta
from typing import (
    Any,
    Callable,
    Iterable,
    Optional,
    Type,
    Union,
    Dict,
    Sequence,
)

from . import _qt as api

# ######### decorator ######### #

ChoicesType = Union[EnumMeta, Iterable, Callable[[Type], Iterable]]
_TYPE_DEFS: Dict[type, Type[api.WidgetType]] = {}
_CHOICES: Dict[type, ChoicesType] = {}
_NONE = object()  # stub to detect if a user passed None to an optional param


def magicgui(
    function: Callable = None,
    layout: Union[api.Layout, str] = "horizontal",
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    parent: api.WidgetType = None,
    **param_options: dict,
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
            if hasattr(func, "_widget"):
                # a widget has been instantiated
                return func._widget(*args, **kwargs)
            return func(*args, **kwargs)

        class MagicGui(MagicGuiBase):
            if hasattr(func, "__name__"):
                __doc__ = f'MagicGui generated for function "{func.__name__}"'

            def __init__(self, show=False) -> None:
                super().__init__(
                    func,
                    layout=_layout,
                    call_button=call_button,
                    auto_call=auto_call,
                    **param_options,
                )
                wrapper.called = self.called
                if show:
                    self.show()

        wrapper.Gui = MagicGui
        return wrapper

    return inner_func if function is None else inner_func(function)


# ######### Base MagicGui Class ######### #


class WidgetDescriptor:
    """A descriptor to translate get/set calls into appropriate API for the widget.

    How to use:
    This descriptor is instantiated with the name of an attribute on the parent class.
    (see, for example: MagicGuiBase.add_widget_descriptor).  This descriptor assumes
    that the obj passed to the __get__/__set__ methods (i.e. the instance), has an
    attribute named `WIDGET_ATTR.format(self.name)`.  If not, it will raise an
    AttributeError. When `self.name` as accessed on the parent class, this descriptor
    access the appropriate getter/setter on the widget instance.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __get__(self, obj, objtype) -> Any:
        widget = obj.get_widget(self.name)
        return api.getter_setter_onchange(widget).getter()

    def __set__(self, obj, val) -> None:
        widget = obj.get_widget(self.name)
        if api.is_categorical(widget):
            val = api.get_categorical_index(widget, val)
        return api.getter_setter_onchange(widget).setter(val)

    def __delete__(self, obj) -> None:
        widget = obj.get_widget(self.name)
        obj.layout().removeWidget(widget)
        widget.deleteLater()
        delattr(type(obj), self.name)


class MagicGuiBase(api.WidgetType):

    called = api.Signal(object)  # result of the function call
    parameter_updated = api.Signal()  # name of the parameter that was changed

    WIDGET_ATTR = "{}_widget"

    def __init__(
        self,
        func: Callable,
        *,
        layout: api.Layout = api.Layout.horizontal,
        call_button: Union[bool, str] = False,
        auto_call: bool = False,
        parent: api.WidgetType = None,
        ignore: Optional[Sequence[str]] = None,
        **param_options: Dict[str, Dict[str, Any]],
    ) -> None:
        super().__init__(parent=parent)
        # this is how the original function object knows that an object has been created
        setattr(func, "_widget", self)
        self.func = func
        self.setLayout(layout.value(self))
        self.param_options = param_options
        sig = inspect.signature(func)

        # TODO: should we let required positional args get skipped?
        self.param_names = tuple(p for p in sig.parameters if p not in (ignore or []))
        for param in sig.parameters.values():
            if param.name not in self.param_names:
                continue
            self.set_widget(
                name=param.name,
                value=(None if param.default is param.empty else param.default),
                dtype=(None if param.annotation is param.empty else param.annotation),
            )

        if call_button:
            self.call_button = api.ButtonType(
                call_button if isinstance(call_button, str) else "call"
            )
            self.call_button.clicked.connect(self.__call__)
            self.layout().addWidget(self.call_button)

        if auto_call:
            self.parameter_updated.connect(self.__call__)

    def set_widget(
        self,
        name: str,
        value: Optional[Any] = None,
        position: Optional[int] = None,
        dtype: Optional[Type] = None,
        widget_type: Optional[api.WidgetType] = None,
        options: Optional[Dict[str, ChoicesType]] = None,
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
        options = options or self.param_options.get(name) or dict()
        _widget_type = widget_type or options.get("widget_type")
        dtype = dtype or options.get("dtype")

        if dtype is not None:
            arg_type = dtype
        elif value is not None:
            arg_type: Type = type(value)
        else:
            arg_type = type(None)

        # TODO: move choices logic out of this method
        # argument specific choices override _CHOICES registered with `register_type`
        _choices = options.get("choices") or _type2choices(arg_type)
        choices = _choices(arg_type) if callable(_choices) else _choices  # type: ignore
        if _widget_type:
            WidgetType = _widget_type
        elif choices:
            if (value is not None) and (value not in choices):
                raise ValueError(
                    '"choices" option was provided, but the default value '
                    f"({value}) was not in the provided choices "
                    f"{choices}"
                )
            WidgetType = api.get_categorical_widget()
        else:
            try:
                WidgetType = type2widget(arg_type)
            except TypeError:
                raise TypeError(
                    "Unable to find the appropriate widget for arg "
                    f'"{name}", type "{arg_type}" '
                )

        existing_widget = self.get_widget(name, None)
        # if there is already a widget by this name...
        if existing_widget:
            # if it has the same widget type as the new one, update the value
            if isinstance(existing_widget, WidgetType):
                return setattr(self, name, value)
            # otherwise delete it, but get the position so we can insert the new one.
            else:
                position = self.layout().indexOf(existing_widget)
                delattr(self, name)

        # create a new widget
        widget = api.make_widget(WidgetType, name=name, parent=self, **options)

        # connect on_change signals
        change_signal = api.getter_setter_onchange(widget).onchange
        setattr(self, f"{name}_changed", change_signal)
        change_signal.connect(lambda: self.parameter_updated.emit())

        # add widget to class and make descriptor
        setattr(self, self.WIDGET_ATTR.format(name), widget)
        self.add_widget_descriptor(name)

        # update choices if it's a categorical
        if choices or isinstance(arg_type, EnumMeta):
            if callable(_choices):
                setattr(widget, "_get_choices", functools.partial(_choices, arg_type))  # type: ignore # noqa: E501
            self.set_choices(name, choices or arg_type)  # type: ignore

        if value is not None:
            setattr(self, name, value)
        if position is not None:
            if not isinstance(position, int):
                raise TypeError(
                    f"`position` argument must be of type int. got: {type(position)}"
                )
            if position < 0:
                position = self.layout().count() + position + 1
            self.layout().insertWidget(position, widget)
        else:
            self.layout().addWidget(widget)

        return widget

    @classmethod
    def add_widget_descriptor(cls, name: str) -> None:
        setattr(cls, name, WidgetDescriptor(name))

    def get_widget(self, name: str, default: Any = _NONE) -> Optional[api.WidgetType]:
        widget = getattr(self, self.WIDGET_ATTR.format(name), default)
        if widget is _NONE:
            raise AttributeError(
                f"{self.__class__.__name__} has no widget named '{name}''."
            )
        return widget

    def fetch_choices(self, name: str) -> None:
        """update choices if a callable has been provided... otherwise raise."""
        widget = self.get_widget(name)
        if not hasattr(widget, "_get_choices"):
            raise TypeError(
                f"Widget '{name}' was not provided with a callable to get choices."
            )
        self.set_choices(name, widget._get_choices())

    def set_choices(self, name, choices: ChoicesType) -> None:
        widget = self.get_widget(name)
        if not api.is_categorical(widget):
            raise TypeError(f"'{name}' is not a categorical widget with choices.")
        if isinstance(choices, EnumMeta):
            api.set_categorical_choices(widget, [(x.name, x) for x in choices])
        else:
            api.set_categorical_choices(widget, [(str(c), c) for c in choices])  # type: ignore # noqa: E501

    @property
    def current_kwargs(self) -> dict:
        return {param: getattr(self, param) for param in self.param_names}

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


def register_type(
    type_: type,
    *,
    widget_type: Optional[Type[api.WidgetType]] = None,
    choices: Optional[ChoicesType] = None,
) -> None:
    if widget_type is None and choices is None:
        raise ValueError("either `widget_type` or `choices` must be provided.")

    if choices is not None:
        _CHOICES[type_] = choices
        _TYPE_DEFS[type_] = api.get_categorical_widget()
        if widget_type is not None:
            warnings.warn(
                "Providing `choices` overrides `widget_type`. Categorical widget will "
                f"be used: {_TYPE_DEFS[type_]}"
            )
    else:
        _TYPE_DEFS[type_] = widget_type


def reset_type(type_):
    global _TYPE_DEFS
    global _CHOICES
    del _TYPE_DEFS[type_]
    del _CHOICES[type_]


def _type2widget(type_: type) -> Optional[Type[api.WidgetType]]:
    # look for direct hits
    if type_ in _TYPE_DEFS:
        return _TYPE_DEFS[type_]
    # look for subclasses
    for registered_type in _TYPE_DEFS:
        # TODO: is it necessary to check for isclass at this point?
        if inspect.isclass(type_) and issubclass(type_, registered_type):
            return _TYPE_DEFS[registered_type]


def _type2choices(type_: type) -> Optional[ChoicesType]:
    # look for direct hits
    if type_ in _CHOICES:
        return _CHOICES[type_]
    # look for subclasses
    for registered_type in _CHOICES:
        # TODO: is it necessary to check for isclass at this point?
        if inspect.isclass(type_) and issubclass(type_, registered_type):
            return _CHOICES[registered_type]


def type2widget(type_: type) -> Type[api.WidgetType]:
    WidgetType = _type2widget(type_)
    if not WidgetType:
        WidgetType = api.type2widget(type_)
    if not WidgetType:
        raise TypeError(f'Unable to convert type "{type_}" into a widget.')
    return WidgetType
