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


def type2widget(type_: type) -> Type[api.WidgetType]:
    WidgetType = api.type2widget(type_)
    if not WidgetType:
        raise TypeError(f'Unable to convert type "{type_}" into a widget.')
    return WidgetType


class WidgetDescriptor:
    def __init__(self, widget: api.WidgetType, name: Optional[str] = None) -> None:
        self.widget = widget
        self.name = name
        self.getter, self.setter, self.onchange = api.getter_setter_onchange(widget)

    def __get__(self, obj, objtype) -> Any:
        return self.getter()

    def __set__(self, obj, val) -> None:
        if api.is_categorical(self.widget):
            val = api.get_categorical_index(self.widget, val)
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
        _widget_attr = name + "_widget"

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
        existing_widget = getattr(self, _widget_attr, None)
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

        widget = WidgetType(parent=self)
        setattr(self, _widget_attr, widget)
        if choices:
            api.set_categorical_choices(widget, zip(choices, choices))
        elif issubclass(arg_type, Enum):
            api.set_categorical_choices(widget, [(x.name, x) for x in arg_type])

        self.add_widget_descriptor(name, widget)
        if value is not None:
            setattr(self, name, value)
        if position is not None:
            self.layout().insertWidget(position, widget)
        else:
            self.layout().addWidget(widget)

        return widget

    @classmethod
    def add_widget_descriptor(cls, name, widget):
        setattr(cls, name, WidgetDescriptor(widget, name))

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

    def __repr__(self):
        return f"<MagicGui for '{self.func.__name__}' at {id(self)}>"


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
        class MagicGui(MagicGuiBase):
            __doc__ = f'MagicGui generated for function "{func.__name__}"'

            def __init__(self) -> None:
                super().__init__(
                    func, layout=_layout, call_button=call_button, **kwargs
                )

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
