"""`guiclass` decorator.

1. Turns a class into a dataclass
2. Uses `psygnal.evented` to make it an [evented
   dataclass](https://psygnal.readthedocs.io/en/latest/dataclasses/)
2. Adds a `gui` property to the class that will return a `magicgui` widget, bound to
the values of the dataclass instance.
"""

from __future__ import annotations

import contextlib
import warnings
from dataclasses import Field, dataclass, field, is_dataclass
from typing import TYPE_CHECKING, Any, Callable, ClassVar, TypeVar, overload
from weakref import WeakKeyDictionary

from psygnal import SignalGroup, SignalInstance, evented, is_evented
from psygnal import __version__ as psygnal_version

from magicgui.schema._ui_field import build_widget
from magicgui.widgets import PushButton
from magicgui.widgets.bases import BaseValueWidget, ContainerWidget

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from typing import Protocol

    from typing_extensions import TypeGuard

    # fmt: off
    class GuiClassProtocol(Protocol):
        """Protocol for a guiclass."""

        @property
        def gui(self) -> ContainerWidget: ...
        @property
        def events(self) -> SignalGroup: ...
    # fmt: on

__all__ = ["button", "guiclass", "is_guiclass", "unbind_gui_from_instance"]
_BUTTON_ATTR = "_magicgui_button"
_GUICLASS_FLAG = "__magicgui_guiclass__"

_T = TypeVar("_T")
T = TypeVar("T", bound="type[Any]")
F = TypeVar("F", bound=Callable)


if psygnal_version.split(".")[:2] < ["0", "8"]:
    _IGNORE_REF_ERR = {}
else:
    _IGNORE_REF_ERR = {"on_ref_error": "ignore"}


# https://github.com/microsoft/pyright/blob/main/specs/dataclass_transforms.md
def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_specifiers: tuple[type | Callable[..., Any], ...] = (()),
) -> Callable[[_T], _T]:
    return lambda a: a


@__dataclass_transform__(field_specifiers=(Field, field))
@overload
def guiclass(cls: T) -> T: ...


@__dataclass_transform__(field_specifiers=(Field, field))
@overload
def guiclass(
    *,
    gui_name: str = "gui",
    events_namespace: str = "events",
    follow_changes: bool = True,
    **dataclass_kwargs: Any,
) -> Callable[[T], T]: ...


def guiclass(
    cls: T | None = None,
    *,
    gui_name: str = "gui",
    events_namespace: str = "events",
    follow_changes: bool = True,
    **dataclass_kwargs: Any,
) -> T | Callable[[T], T]:
    """Turn class into a dataclass with a property (`gui_name`) that returns a gui.

    This decorator is similar to `dataclasses.dataclass`, but it will also add an
    `events` attribute to the class that is an instance of `psygnal.SignalGroup` (with a
    signal for each field in the dataclass; see
    https://psygnal.readthedocs.io/en/latest/dataclasses/ for details), and a `gui`
    property that returns a `magicgui` widget, bound to the values of the dataclass
    instance.

    !!! note
        This decorator is compatible with dataclasses using `slots=True`, however,
        there is a potential for a memory leak that the user should be aware of.
        If you create a `guiclass` instance, and then store a reference to its `gui`,
        and then delete the instance, the `gui` will still be bound to the instance,
        preventing it from being garbage collected.  To avoid this, you can call
        `unbind_gui_from_instance(gui, instance)` before deleting the instance.

    Parameters
    ----------
    cls : type
        The class to turn into a dataclass.
    gui_name : str, optional
        The name of the property that will return a `magicgui` widget, by default
        `"gui"`
    events_namespace : str, optional
        The name of the attribute that will be added to the class, by default "events".
        This attribute will be an instance of `psygnal.SignalGroup` that will be used
        to connect events to the class.
    follow_changes : bool, optional
        If `True` (default), changes to the dataclass instance will be reflected in the
        gui, and changes to the gui will be reflected in the dataclass instance.
    dataclass_kwargs : dict, optional
        Additional keyword arguments to pass to `dataclasses.dataclass`.

    Returns
    -------
    type
        The dataclass.

    Examples
    --------
    >>> @guiclass
    ... class MyData:
    ...     x: int = 0
    ...     y: str = "hi"
    ...
    ...     @button
    ...     def reset(self):
    ...         self.x = 0
    ...         self.y = "hi"
    >>> data = MyData()
    >>> data.gui.show()
    """

    def _deco(cls: T) -> T:
        if dataclass_kwargs.get("frozen", False):
            raise ValueError(
                "The 'guiclass' decorator does not support dataclasses with "
                "`frozen=True`. If you need this feature, please open an issue at "
                "https://github.com/pyapp-kit/magicgui/issues."
            )

        builder = GuiBuilder(
            gui_name,
            follow_changes=follow_changes,
            events_namespace=events_namespace,
        )
        if not is_dataclass(cls):
            cls = dataclass(cls, **dataclass_kwargs)  # type: ignore
        setattr(cls, gui_name, builder)
        builder.__set_name__(cls, gui_name)
        return cls

    return _deco(cls) if cls is not None else _deco


def is_guiclass(obj: object) -> TypeGuard[GuiClassProtocol]:
    """Return `True` if obj is a guiclass or an instance of a guiclass."""
    return is_dataclass(obj) and hasattr(obj, _GUICLASS_FLAG)


@overload
def button(func: F) -> F: ...


@overload
def button(**kwargs: Any) -> Callable[[F], F]: ...


def button(func: F | None = None, **button_kwargs: Any) -> F | Callable[[F], F]:
    """Add a method as a button to a `guiclass`, which calls the decorated method.

    Parameters
    ----------
    func : callable
        The method to decorate.  If None, returns a decorator that can be applied to a
        method.
    button_kwargs : dict, optional
        Additional keyword arguments to pass to `magicgui.widgets.PushButton`.
    """

    def _deco(func: F) -> F:
        button_kwargs.setdefault("name", func.__name__)
        setattr(func, _BUTTON_ATTR, button_kwargs)
        return func

    return _deco(func) if func else _deco


class GuiBuilder:
    """Descriptor that builds a widget for a dataclass or instance.

    Parameters
    ----------
    name : str, optional
        The name of the property that will return a `magicgui` widget.
        When used as a descriptor, the name of the class-attribute to which this
        descriptor is applied will be used.
    follow_changes : bool, optional
        If `True` (default), changes to the dataclass instance will be reflected in the
        gui, and changes to the gui will be reflected in the dataclass instance.
    events_namespace : str
        If the owner of this descriptor is not already evented when __set_name__ is
        called, it will be be made evented and the events namespace will be set to this
        value. By default, this is "events". (see `psygnal.SignalGroupDescriptor`
        for details.)
    """

    def __init__(
        self,
        name: str = "",
        follow_changes: bool = True,
        events_namespace: str = "events",
    ):
        self._name = name
        self._follow_changes = follow_changes
        self._owner: type | None = None
        self._events_namespace = events_namespace

    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name
        self._owner = owner
        if not is_evented(owner):
            evented(owner, events_namespace=self._events_namespace)
        setattr(owner, _GUICLASS_FLAG, True)

    def widget(self) -> ContainerWidget:
        """Return a widget for the dataclass or instance."""
        if self._owner is None:
            raise TypeError(
                "Cannot call `widget` on an unbound `GuiBuilder` descriptor."
            )
        return build_widget(self._owner)

    def __get__(
        self, instance: object | None, owner: type
    ) -> ContainerWidget[BaseValueWidget] | GuiBuilder:
        if instance is None:
            return self
        wdg = build_widget(instance)

        # look for @button-decorated methods
        # TODO: move inside build_widget?
        for k, v in vars(owner).items():
            if hasattr(v, _BUTTON_ATTR):
                kwargs = getattr(v, _BUTTON_ATTR)
                button = PushButton(**kwargs)
                if instance is not None:
                    # call the bound method if we're in an instance
                    button.clicked.connect(getattr(instance, k))
                else:
                    # TODO: what to do here?
                    # probably doesn't make sense to call the method on the class
                    ...
                # TODO: allow inserting in a specific location
                wdg.append(button)

        if instance is not None and self._name:
            if self._follow_changes:
                bind_gui_to_instance(wdg, instance)
            # cache it on the instance
            # call del instance.<_name> to remove it
            # this may fail in cases of __slots__ other attribute restrictions
            # the cost is that the widget will be rebuilt on each access
            with contextlib.suppress(AttributeError):
                setattr(instance, self._name, wdg)
        return wdg


def bind_gui_to_instance(
    gui: ContainerWidget, instance: Any, two_way: bool = True
) -> None:
    """Set change events in `gui` to update the corresponding attributes in `model`.

    Parameters
    ----------
    gui : ContainerWidget
        The widget to bind to the instance.
    instance : Any
        The instance to bind to the widget.  In most cases, this will be an instance
        of a `guiclass`.
    two_way : bool, optional
        If True, changes to the instance will be reflected in the gui, by default True
    """
    events = getattr(instance, "events", None) if two_way else None
    signals: Mapping[str, SignalInstance] = {}
    if isinstance(events, SignalGroup):
        # psygnal >=0.10
        if hasattr(events, "__iter__") and hasattr(events, "__getitem__"):
            signals = {k: events[k] for k in events}
        else:  # psygnal <0.10
            signals = events.signals

    # in cases of classes with `__slots__`, widget.changed.connect_setattr(instance...)
    # will show a RuntimeWarning because `instance` will not be weak referenceable.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        for widget in gui:
            # would be cleaner to check isinstance(widget, ValueWidget)... but a few
            # widgets (like FileEdit) are not ValueWidgets, but still have a `changed`
            # signal and a value method. So for now we just check for the protocol.
            changed = getattr(widget, "changed", None)

            # we skip PushButton here, otherwise we will set the value of the
            # button (a boolean) to some attribute on the instance, which is probably
            # not what we want.
            if isinstance(changed, SignalInstance) and not isinstance(
                widget, PushButton
            ):
                name: str = getattr(widget, "name", "")
                two_way_obj = TwoWaySetAttr(widget, instance, name)
                # connect changes in the widget to the instance
                if hasattr(instance, name):
                    try:
                        changed.connect(two_way_obj.set_instance_value)
                    except TypeError:
                        warnings.warn(
                            f"Could not bind {name} to {instance}. "
                            "This may be because the instance has __slots__ or "
                            "other attribute restrictions. Please update psygnal.",
                            stacklevel=2,
                        )

                # connect changes from the instance to the widget
                if name in signals:
                    signals[name].connect(two_way_obj.set_widget_value)


class TwoWaySetAttr:
    """Class for setattr operation between widget and instance in guiclass."""

    # NOTE: This global instance container is used for two reasons:
    # 1. To avoid garbage collection after an instance is connected to a psygnal signal
    #    instance.
    # 2. To disconnect callbacks both ways when it is not to be used anymore.
    _all_objs: WeakKeyDictionary[BaseValueWidget, TwoWaySetAttr] = WeakKeyDictionary()

    def __init__(
        self,
        widget: BaseValueWidget,
        instance: Any,
        name: str,
    ):
        if widget in self._all_objs:
            raise ValueError(f"widget {widget!r} is used in multiple guiclasses.")
        self._widget = widget
        self._instance = instance
        self._name = name
        self._is_setting_widget_value = False
        self._is_setting_instance_value = False
        self._all_objs[widget] = self

    def set_widget_value(self, value: Any, *_: Any) -> None:
        """Set given value to widget."""
        if self._is_setting_widget_value:
            # Avoid setting value to widget more than once
            return
        with self.setting_widget_value():
            self._widget.value = value

    def set_instance_value(self, value: Any) -> None:
        """Set given value to instance."""
        if self._is_setting_instance_value:
            # Avoid setting value to instance more than once
            return
        # This method is always called from the `changed` signal of the widget
        # so we also need to enter `setting_widget_value` context.
        with self.setting_instance_value(), self.setting_widget_value():
            setattr(self._instance, self._name, value)

    @contextlib.contextmanager
    def setting_widget_value(self) -> Iterator[None]:
        """Widget value is being set in this context."""
        was_setting = self._is_setting_widget_value
        self._is_setting_widget_value = True
        try:
            yield
        finally:
            self._is_setting_widget_value = was_setting

    @contextlib.contextmanager
    def setting_instance_value(self) -> Iterator[None]:
        """Instance value is being set in this context."""
        was_setting = self._is_setting_instance_value
        self._is_setting_instance_value = True
        try:
            yield
        finally:
            self._is_setting_instance_value = was_setting


def unbind_gui_from_instance(gui: ContainerWidget, instance: Any | None = None) -> None:
    """Unbind a gui from an instance.

    This will disconnect all events that were connected by `bind_gui_to_instance`.
    In cases where `guiclass` is used on a dataclass with `slots=True`, when a reference
    to the gui is stored elsewhere, this must be called by the user before the instance
    is deleted.

    Parameters
    ----------
    gui : ContainerWidget
        The widget bound to `instance`.
    instance : Any
        An instance of a `guiclass`.
    """
    for widget in gui:
        if isinstance(widget, BaseValueWidget):
            TwoWaySetAttr._all_objs.pop(widget, None)


# Class-based form ... which provides subclassing and inheritance (unlike @guiclass)


@__dataclass_transform__(field_specifiers=(Field, field))
class GuiClassMeta(type):
    def __new__(cls: type, name: str, bases: tuple, attrs: dict) -> type:
        attrs[_GUICLASS_FLAG] = True
        obj: type = type.__new__(cls, name, bases, attrs)
        return evented(dataclass(obj))


# evented will warn "No mutable fields found in class <class '__main__.GuiClass'>"
# no events will be emitted... but it will work fine for subclasses.
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=UserWarning)

    class GuiClass(metaclass=GuiClassMeta):
        gui = GuiBuilder()
        if TYPE_CHECKING:
            events: ClassVar[SignalGroup]

            # the mypy dataclass magic doesn't work without the literal decorator
            # it WILL work with pyright due to the __dataclass_transform__ above
            # here we just avoid a false error in mypy
            def __init__(self, *args: Any, **kwargs: Any) -> None: ...
