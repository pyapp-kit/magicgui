# -*- coding: utf-8 -*-
"""Core functionality of magicgui decorator and MagicGui class.

magicgui autogenerates graphical user interfaces (GUIs) from python functions by
introspecting signatures and matching argument types to widgets.  It provides two-way
data-binding, such that modifying the parameters in the gui will change the effective
"default" values in the original function, and changing parameters in the instantiated
widget attributes will change those values in the GUI.

Example
-------
This will create a GUI with an integer (SpinBox) and string (LineEdit) fields.

>>> @magicgui
... def my_function(a: int = 1, b: str = 'hello'):
...     pass
...
... gui = my_function.Gui(show=True)


Attributes
----------
MagicGuiBase : class
    Most of the functionality is defined in this class, though it is not (usually)
    intended to be called directly.

magicgui : callable
    Intended for use as a decorator.  Takes a function and various arguments and creates
    a new MagicGui class (a subclass of MagicGuiBase) appropriate for the function.
    That class is added as an attribute ``Gui`` to the function which can be called to
    instantiate a GUI widget.
"""

from collections import defaultdict
import functools
import inspect
import os
import warnings
from enum import EnumMeta
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    TypeVar,
    Optional,
    Sequence,
    Type,
    Union,
    List,
)

from . import _qt as api

MagicGuiType = TypeVar("MagicGuiType")
ChoicesCallback = Callable[[MagicGuiType, Type], Iterable]
ChoicesType = Union[EnumMeta, Iterable, ChoicesCallback]
_TYPE_DEFS: Dict[type, Type[api.WidgetType]] = {}
_CHOICES: Dict[type, ChoicesType] = {}


SKIP_UNRECOGNIZED_TYPES = os.environ.get("MAGICGUI_SKIP_UNRECOGNIZED_TYPES", False)


# ######### Base MagicGui Class ######### #


class WidgetDescriptor:
    """A descriptor to translate get/set calls into appropriate API for the widget.

    In this design, the widget itself serves as the "source of truth" for the current
    value of a given parameter.

    How to use:
    This descriptor is instantiated with the name of an attribute on the parent class.
    (see, for example: MagicGuiBase._add_widget_descriptor).  This descriptor assumes
    that the obj passed to the __get__/__set__ methods (i.e. the instance), has an
    attribute named `WIDGET_ATTR.format(self.name)`.  If not, it will raise an
    AttributeError. When `self.name` as accessed on the parent class, this descriptor
    access the appropriate getter/setter on the widget instance.
    """

    def __init__(self, name: str) -> None:
        """Create a WidgetDescriptor for the attribute named ``name``.

        Parameters
        ----------
        name : str
            Attribute name.
        """
        self.name = name

    def __get__(self, obj, objtype) -> Any:
        """Get the current value from the widget."""
        widget = obj.get_widget(self.name)
        return api.getter_setter_onchange(widget).getter()

    def __set__(self, obj, val) -> None:
        """Set the current value for the widget."""
        widget = obj.get_widget(self.name)
        if api.is_categorical(widget):
            val = api.get_categorical_index(widget, val)
        return api.getter_setter_onchange(widget).setter(val)

    def __delete__(self, obj) -> None:
        """Remove the widget from the layout, cleanup, and remove from parent class."""
        widget = obj.get_widget(self.name)
        obj.layout().removeWidget(widget)
        widget.deleteLater()
        delattr(type(obj), self.name)


class MagicGuiBase(api.WidgetType):
    """Main base class for MagicGui.

    In most cases, this class will be subclassed into a useable MagicGui when the
    magicgui decorator is called on a function.
    """

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
        """Instantiate a MagicGui widget.

        Parameters
        ----------
        func : Callable
            The function being decorated
        layout : api.Layout, optional
            The type of layout to use, by default api.Layout.horizontal
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
        """
        super().__init__(parent=parent)
        # this is how the original function object knows that an object has been created
        setattr(func, "_widget", self)
        self.param_names = []
        self._result_name: str = ""
        # Optional mapping of parameter name -> valid choices for that parameter
        self._choices: Dict[str, ChoicesType] = dict()
        # mapping of param name, parameter type.  Will be set in set_widget.
        self._arg_types: Dict[str, Type] = dict()
        self.func = func
        self.setLayout(layout.value(self))
        self.param_options = param_options

        # TODO: should we let required positional args get skipped?
        for param in inspect.signature(func).parameters.values():
            if param.name in (ignore or []):
                continue
            self.set_widget(
                name=param.name,
                value=(None if param.default is param.empty else param.default),
                dtype=(None if param.annotation is param.empty else param.annotation),
            )
            self.param_names.append(param.name)

        if call_button:
            self.call_button = api.ButtonType(
                call_button if isinstance(call_button, str) else "call"
            )
            # using lambda because the clicked signal returns a value
            self.call_button.clicked.connect(lambda checked: self.__call__())
            self.layout().addWidget(self.call_button)

        # a convenience, allows widgets to change their choices depending on context
        # particularly useful if a downstream library has registered a type with a
        # choices function that traverses the parent tree for context.
        self.parentChanged.connect(self.refresh_choices)

        if auto_call:
            self.parameter_updated.connect(self.__call__)

    def set_widget(
        self,
        name: str,
        value: Optional[Any] = None,
        position: Optional[int] = None,
        dtype: Optional[Type] = None,
        widget_type: Optional[Type[api.WidgetType]] = None,
        options: Optional[dict] = None,
    ) -> Optional[api.WidgetType]:
        """Make a widget named ``name`` with value ``value``.  If exists, set value.

        A descriptor will also be added as an attribute to this class (named `name`).
        The descriptor provides the __get__ and __set__ methods that enable updating the
        GUI by simply setting the attribute on the MagicGui instance that has the same
        name as the argument in the function signature.

        The argument type (which determines which GUI widget type will be used), is
        inferred in this order:
            1. if the ``dtype`` argument is provided, use it.
            2. if not, if a ``dtype`` key is present in the ``options`` dict, use it.
            3. if not, if ``value`` is provided, dtype = type(value)
            4. otherwise, use type = type(None)  (fallback to the api NoneType widget)

        The Widget type is inferred in this order:
            1. if ``widget_type`` is not None, use it.
            2. if not, if a ``widget_type`` key is present in the ``options`` dict, use
               it.
            3. if not, if a ``choices`` key is present in the ``options`` dict, use the
               default categorical widget type for the current backend (e.g. QComboBox)
            4. if not, call ``type2widget(dtype)`` the ``arg_type`` which isinferred as
               described above.  See docstring for ``type2widget``.
            5. if a widget type is stil not found. raise a TypeError.

        Parameters
        ----------
        name : str
            the name of the parameter for which to s
        value : Any, optional
            The initial value for this parameter, by default None
        position : int, optional
            Position to insert this widget in the layout, by default will be appended to
            the end of the layout.
        dtype : type, optional
            Type for this parameter.  See Summary above for order of type inference if
            dtype is None.
        widget_type : api.WidgetType, optional
            Optional widget_type override.  If None, ``type2widget`` will be called on
            dtype to determine the widget type. by default None
        options : dict, optional
            Optional dict with argument-specific options.  If not provided, if ``name``
            exists in self.param_options (i.e. if the magicgui was created with some
            argument-specific options for this parameter), then those options will be
            used.  Possible keys in this dict include:
                dtype: overrides the argument type
                widget_type: overrides the widget type
                choices: sets this widget to a categorical type, and provides a list of
                         valid choices, or a function to retrieve those choices.

            TODO: consider removing the options arg, and making ``choices`` an arg.
                  then would need to pass **kwargs to api.make_widget

        Returns
        -------
        api.WidgetType
            The instantiated widget. The widget instance is also added to the current
            class instance using setattr(self, self.WIDGET_ATTR.format(name), widget).
        None
            If SKIP_UNRECOGNIZED_TYPES == True (which may be set by the environmental
            variable "MAGICGUI_SKIP_UNRECOGNIZED_TYPES"), then ``None`` will be returned
            when a widget cannot be determined for the current parameter.  Otherwise,
            TypeError is raised.

        Raises
        ------
        ValueError
            If ``choices`` is provided, but the default value is not in the choices.
        TypeError
            If an appropriate widget type cannot be found and SKIP_UNRECOGNIZED_TYPES is
            False.
        TypeError
            If ``position`` is provided but is not an integer.
        """
        _options: dict = options or self.param_options.get(name) or dict()
        _widget_type = widget_type or _options.get("widget_type")
        dtype = dtype or _options.get("dtype")

        if dtype is not None:
            arg_type: Type = dtype
        elif value is not None:
            arg_type = type(value)
        else:
            arg_type = type(None)

        self._arg_types[name] = arg_type

        # argument specific choices override _CHOICES registered with `register_type`
        choices: Optional[ChoicesType] = (
            _options.get("choices")
            or _type2choices(arg_type)
            or (arg_type if isinstance(arg_type, EnumMeta) else None)
        )
        if choices:
            self.set_choices(name, choices)
            WidgetType = api.get_categorical_widget()

            # make sure any default value provided is actually in the choices.
            _choices = self.get_choices(name)
            if (value is not None) and (value not in _choices):
                raise ValueError(
                    '"choices" option was provided, but the default value '
                    f"({value}) was not in the provided choices "
                    f"{_choices}"
                )
        elif _widget_type:
            WidgetType = _widget_type
        else:
            try:
                WidgetType = type2widget(arg_type)
            except TypeError:
                msg = (
                    "Unable to find the appropriate widget for function "
                    f'"{self.func.__name__}", arg "{name}", type "{arg_type}".'
                )
                if SKIP_UNRECOGNIZED_TYPES:
                    warnings.warn(msg + " Skipping.")
                    return None
                raise TypeError(msg)

        # check if there is already am existintg widget by this name...
        try:
            existing_widget: Optional[api.WidgetType] = self.get_widget(name)
        except AttributeError:
            existing_widget = None
        if existing_widget:
            # if it has the same widget type as the new one, update the value
            if isinstance(existing_widget, WidgetType):
                setattr(self, name, value)
                return existing_widget
            # otherwise delete it, but get the position so we can insert the new one.
            else:
                position = self.layout().indexOf(existing_widget)
                delattr(self, name)

        # instantiate a new widget
        widget = api.make_widget(WidgetType, name=name, parent=self, **_options)

        # connect on_change signals
        change_signal = api.getter_setter_onchange(widget).onchange
        setattr(self, f"{name}_changed", change_signal)
        change_signal.connect(lambda: self.parameter_updated.emit())

        # add widget attribute and make descriptor
        setattr(self, self.WIDGET_ATTR.format(name), widget)
        self._add_widget_descriptor(name)

        # if choices were provided, update the options in the widget.
        if self.has_choices(name):
            self.refresh_choices(name)

        # set the initial value
        if value is not None:
            setattr(self, name, value)

        # add the widget to the layout (appended, or at a specific position)
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
    def _add_widget_descriptor(cls, name: str) -> None:
        setattr(cls, name, WidgetDescriptor(name))

    def get_widget(self, name: str) -> api.WidgetType:
        """Get widget instance for parameter named ``name``."""
        try:
            return getattr(self, self.WIDGET_ATTR.format(name))
        except AttributeError:
            cls_name = self.__class__.__name__
            raise AttributeError(f"{cls_name} has no widget named '{name}'.")

    def refresh_choices(
        self, names: Optional[Union[str, Sequence[str]]] = None
    ) -> None:
        """Update the GUI choices for all widgets or all parameters in ``names``.

        Parameters
        ----------
        names : str or sequence of str, optional
            An attribute name or list of attribute names for which to update choices.
            Must be one of the parameters with registered choices.  by default, all
            registered choices will be updated.

        Raises
        ------
        ValueError
            If a name is provided that does not have registered choices.
        """
        if isinstance(names, str):
            names = [names]
        if names:
            bad_names = [name for name in names if not self.has_choices(name)]
            if bad_names:
                raise ValueError(
                    "Cannot update choices for parameters without "
                    f"registered choices: '{bad_names}'"
                )
        else:
            names = list(self._choices.keys())

        for name in names:
            widget = self.get_widget(name)
            choices = self.get_choices(name)
            # choices are set as (name, data) tuples because we assume DataComboBox
            if isinstance(choices, EnumMeta):
                # TODO: figure out typing on Enums
                api.set_categorical_choices(widget, [(x.name, x) for x in choices])  # type: ignore  # noqa
            else:
                api.set_categorical_choices(widget, [(str(c), c) for c in choices])

    def has_choices(self, name: str) -> bool:
        """Return True if choices have been registered for parameter ``name``."""
        return name in self._choices

    def get_choices(self, name: str) -> Union[EnumMeta, Iterable]:
        """Get possible choices for parameter ``name``.

        If a function was originally supplied as an argument for ``choices``, then the
        function will be called at this point.  If an Enum was provided, the Enum
        class will be returned.

        Parameters
        ----------
        name : str
            The name of the parameter for which to receive choices

        Returns
        -------
        iterable or enum
            The list of choices for this parameter.  May be an Enum class.

        Raises
        ------
        KeyError
            If no choices have been registered
        """
        try:
            choices = self._choices[name]
        except KeyError:
            raise KeyError(f"No choices have been registered for parameter '{name}'")

        if not isinstance(choices, EnumMeta) and callable(choices):
            return choices(self, self._arg_types[name])
        return choices

    def set_choices(self, name: str, choices: ChoicesType) -> None:
        """Set possible choices for parameter ``name``."""
        if not choices:
            raise ValueError("choices cannot be None")
        if not (callable(choices) or hasattr(choices, "__iter__")):
            raise TypeError(
                f'Cannot set choices for "{name}" to "{choices}". Choices must be '
                "either an iterable or a callable that returns an iterable."
            )

        self._choices[name] = choices

    @property
    def current_kwargs(self) -> dict:
        """Get the current values in the gui to pass to a function call."""
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

        return_type = self.func.__annotations__.get("return")
        if return_type:
            for callback in _type2callback(return_type):
                callback(self, value, return_type)
        return value

    def _current_signature(self):
        """Return the oritinal function signature, using current values from the GUI."""
        return (
            f'({", ".join([f"{n}={repr(k)}" for n, k in self.current_kwargs.items()])})'
        )

    @property
    def result_name(self) -> str:
        """Return a name that can be used for the result of this magicfunction."""
        return self._result_name or (self.func.__name__ + " result")

    @result_name.setter
    def result_name(self, value: str):
        """Set the result name of this MagicGui widget."""
        self._result_name = value

    def __repr__(self):
        """Representation of the MagicGui with current function signature."""
        func_string = f"{self.func.__name__}{self._current_signature()}"
        return f"<MagicGui: {func_string}>"


# ######### magicgui decorator ######### #


# TODO: make protocol
# class MagicFunction(Protocol):
#     Gui: MagicGuiBase


def magicgui(
    function: Optional[Callable] = None,
    layout: Union[api.Layout, str] = "horizontal",
    call_button: Union[bool, str] = False,
    auto_call: bool = False,
    parent: api.WidgetType = None,
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
    for key, value in param_options.items():
        if not isinstance(value, dict):
            raise TypeError(f"value for keyword argument {key} should be a dict")

    _layout = api.Layout[layout] if isinstance(layout, str) else layout

    def inner_func(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if hasattr(func, "_widget"):
                # a widget has been instantiated
                return getattr(func, "_widget")(*args, **kwargs)
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
    return inner_func(function)


# ######### UTILITY FUNCTIONS ######### #


ReturnCallback = Callable[[MagicGuiBase, Any, Type], None]
_RETURN_CALLBACKS: DefaultDict[type, List[ReturnCallback]] = defaultdict(list)


def register_type(
    type_: type,
    *,
    widget_type: Optional[Type[api.WidgetType]] = None,
    choices: Optional[ChoicesType] = None,
    return_callback: Optional[ReturnCallback] = None,
) -> None:
    """Register a ``widget_type`` to be used for all parameters with type ``type_``.

    Parameters
    ----------
    type_ : type
        The type for which a widget class or return callback will be provided.
    widget_type : Optional[Type[api.WidgetType]], optional
        A widget class from the current backend that should be used whenever ``type_``
        is used as the type annotation for an argument in a decorated function,
        by default None
    choices : enum or iterable or callable, optional
        If provided, a categorical type widget will always be used for arguments of type
        ``type_``, and ``choices`` will be used to populate the widget.
        By default None.
    return_callback: callable, optional
        If provided, whenever ``type_`` is declared as the return type of a decorated
        function, ``return_callback(widget, value, return_type)`` will be called
        whenever the decorated function is called... where ``widget`` is the MagicGui
        instance, and ``value`` is the return value of the decorated function.

    Raises
    ------
    ValueError
        If both ``widget_type`` and ``choices`` are None
    """
    if not (return_callback or choices or widget_type):
        raise ValueError(
            "One of `widget_type`, `choices`, or `return_callback` must be provided."
        )

    if return_callback is not None:
        _RETURN_CALLBACKS[type_].append(return_callback)

    if choices is not None:
        _CHOICES[type_] = choices
        _TYPE_DEFS[type_] = api.get_categorical_widget()
        if widget_type is not None:
            warnings.warn(
                "Providing `choices` overrides `widget_type`. Categorical widget will "
                f"be used: {_TYPE_DEFS[type_]}"
            )
    elif widget_type is not None:
        _TYPE_DEFS[type_] = widget_type
    return None


def reset_type(type_):
    """Clear any previously-registered widget types and callbacks for ``type_``."""
    _TYPE_DEFS.pop(type_, None)
    _CHOICES.pop(type_, None)
    _RETURN_CALLBACKS.pop(type_, None)


def _type2choices(type_: type) -> ChoicesType:
    """Check if choices have been registered for ``type_`` and return if so.

    Parameters
    ----------
    type_ : type
        The type_ to look up.

    Returns
    -------
    iterable or callable or None
        A choices lookup iterable or callable.
    """
    # look for direct hits
    if type_ in _CHOICES:
        return _CHOICES[type_]
    # look for subclasses
    for registered_type in _CHOICES:
        # TODO: is it necessary to check for isclass at this point?
        if inspect.isclass(type_) and issubclass(type_, registered_type):
            return _CHOICES[registered_type]
    return []


def _type2callback(type_: type) -> List[ReturnCallback]:
    """Check if return callbacks have been registered for ``type_`` and return if so.

    Parameters
    ----------
    type_ : type
        The type_ to look up.

    Returns
    -------
    list of callable
        Where a return callback accepts two arguments (gui, value) and does something.
    """
    # look for direct hits
    if type_ in _RETURN_CALLBACKS:
        return _RETURN_CALLBACKS[type_]
    # look for subclasses
    for registered_type in _RETURN_CALLBACKS:
        if inspect.isclass(type_) and issubclass(type_, registered_type):
            return _RETURN_CALLBACKS[registered_type]
    return []


def type2widget(type_: type) -> Type[api.WidgetType]:
    """Retrieve the WidgetType for argument type ``type_``.

    Lookup occurs in this order:
        1. If a widget type has been manually registered for ``type_`` using
           ``register_type()``, return it.
        2. If ``type_`` is a subclass of another registered type, return the widget type
           registered for that superclass.
        3. If the current GUI backend (e.g. Qt) declares a widget type for ``type_``,
           return it.
        4. If no match has been found, raise a TypeError.

    Parameters
    ----------
    type_ : type
        The argument type to look up

    Returns
    -------
    Type[api.WidgetType]
        A widget class for the current backend that can be instantiated.

    Raises
    ------
    TypeError
        If no matching widget type can be found for ``type_``.
    """
    # look for direct hits registered by the user
    if type_ in _TYPE_DEFS:
        return _TYPE_DEFS[type_]

    # look for subclasses
    for registered_type in _TYPE_DEFS:
        # TODO: is it necessary to check for isclass at this point?
        if inspect.isclass(type_) and issubclass(type_, registered_type):
            return _TYPE_DEFS[registered_type]

    # get default widget defined by current backend
    WidgetType = api.type2widget(type_)
    if not WidgetType:
        raise TypeError(f'Unable to retrieve widget type for argument type "{type_}".')
    return WidgetType
