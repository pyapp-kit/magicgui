import functools
import inspect
from enum import Enum
from typing import (
    Any,
    Callable,
    Sequence,
    Type,
    Union,
    Optional,
)

from qtpy.QtWidgets import QHBoxLayout

from . import _qt as api


def rsetattr(obj, attr, val):
    pre, _, post = attr.rpartition(".")
    return setattr(rgetattr(obj, pre) if pre else obj, post, val)


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


class WidgetDescriptor:
    def __init__(self, widget: api.WidgetType, name: Optional[str] = None) -> None:
        self.widget = widget
        self.name = name
        self.getter, self.setter, self.onchange = api.getter_setter_onchange(widget)

    def __get__(self, obj, objtype) -> Any:
        return self.getter()

    def __set__(self, obj, val) -> None:
        self.setter(val)

    def __delete__(self, obj) -> None:
        self.widget.parent().layout().removeWidget(self.widget)
        self.widget.deleteLater()
        if self.name:
            delattr(type(obj), self.name)


class MagicGuiBase(api.WidgetType):

    called = api.Signal(object)

    def __init__(
        self,
        func: Callable,
        *,
        layout=QHBoxLayout,
        call_button=False,
        parent=None,
        **kwargs: dict,
    ) -> None:
        super().__init__(parent=parent)
        self.func = func
        setattr(func, "widget", self)
        self.setLayout(layout.value(self))
        self.arg_options = kwargs
        self.params = inspect.signature(func).parameters
        self._params_to_widgets(func)
        if call_button:
            self.call_button = api.ButtonType("call")
            self.call_button.clicked.connect(self.__call__)
            self.layout().addWidget(self.call_button)

    @property
    def _kwargs(self):
        return {
            param.name: getattr(self, param.name)
            for param in self.params.values()
            if param.default is not param.empty
        }

    @property
    def _args(self):
        return list(
            getattr(self, param.name)
            for param in self.params.values()
            if param.default is param.empty
        )

    def __call__(self, *args, **kwargs) -> Any:
        """Call the original function with the current parameter values from the Gui.

        Returns
        -------
        Any
            whatever the return value of the original function would have been.
        """
        _args = self._args
        _kwargs = self._kwargs
        for n, arg in enumerate(args):
            _args[n] = arg
        _kwargs.update(kwargs)
        value = self.func(*_args, **_kwargs)
        self.called.emit(value)
        return value

    def _params_to_widgets(self, func: Callable) -> None:
        """Create a widget for each parameter in the function signature

        For each parameter a descriptor will be added as an attribute to this class
        with the same name as the parameter.  The descriptor provides the __get__ and
        __set__ methods that enable updating the GUI by simply setting the attribute
        on the MagicGui instance that has the same name as the argument in the function
        signature.

        Parameters
        ----------
        func : Callable
            The function to introspect.
        """
        for param in self.params.values():
            arg_opts = self.arg_options.get(param.name, {})
            widget = self._make_widget_from_param(param, **arg_opts)
            setattr(self, param.name + "_widget", widget)
            setattr(MagicGuiBase, param.name, WidgetDescriptor(widget, param.name))
            if param.default is not param.empty:
                setattr(self, param.name, param.default)
            self.layout().addWidget(widget)

    def _make_widget_from_param(
        self, param: inspect.Parameter, choices: Optional[Sequence[str]] = None,
    ) -> api.WidgetType:
        """Make a widget named `name` based on the type of signature param.

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
        if choices:
            if (param.default is not param.empty) and (param.default not in choices):
                raise ValueError(
                    '"choices" option was provided, but the default value '
                    f"({param.default}) was not in the provided choices "
                    f"{choices}"
                )
            arg_type = Enum
        elif param.annotation is not param.empty:
            arg_type = param.annotation
        elif param.default is not param.empty:
            arg_type = type(param.default)
        else:
            arg_type = type(None)

        WidgetType = api.type2widget(arg_type)
        if not WidgetType:
            raise TypeError(f'Unable to convert type "{arg_type}" into a widget.')

        widget = WidgetType(parent=self)
        if choices:
            api.set_combo_choices(widget, choices)
        elif issubclass(arg_type, Enum):
            api.set_combo_choices(widget, arg_type._member_names_)
        return widget

    def __repr__(self):
        return f"<MagicGui for '{self.func.__name__}' at {id(self)}>"


def magicgui(
    function: Callable = None,
    layout: Union[api.Layout, str] = "horizontal",
    call_button: bool = False,
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
        class MagicGui(MagicGuiBase):
            __doc__ = f'MagicGui generated for function "{func.__name__}"'

            def __init__(self) -> None:
                super().__init__(
                    func, layout=_layout, call_button=call_button, **kwargs
                )
                # set descriptors
                for param in self.params:
                    widget = getattr(self, param + "_widget")
                    setattr(MagicGui, param, WidgetDescriptor(widget, param))

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if hasattr(func, "widget"):
                # a widget has been instantiated
                return func.widget(*args, **kwargs)
            return func(*args, **kwargs)

        setattr(wrapper, "Gui", MagicGui)

        def show_gui():
            widget = MagicGui()
            widget.show()
            return widget

        setattr(wrapper, "show", show_gui)

        return wrapper

    return inner_func if function is None else inner_func(function)
