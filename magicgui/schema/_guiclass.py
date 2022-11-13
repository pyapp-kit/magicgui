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
from dataclasses import dataclass, field, is_dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from psygnal import SignalGroup, evented

from magicgui.widgets import PushButton
from magicgui.widgets.bases import ContainerWidget, ValueWidget

from ._ui_field import build_widget

if TYPE_CHECKING:
    from typing import Protocol

    from typing_extensions import TypeGuard

    # fmt: off
    class Guiclass(Protocol):
        """Protocol for a guiclass."""

        @property
        def gui(self) -> ContainerWidget: ...  # noqa: E704
        @property
        def events(self) -> SignalGroup: ...  # noqa: E704
    # fmt: on


__all__ = ["guiclass", "button"]
_BUTTON_ATTR = "_magicgui_button"
_GUICLASS_FLAG = "__magicgui_guiclass__"

_T = TypeVar("_T")
T = TypeVar("T", bound=Type[Any])
F = TypeVar("F", bound=Callable)


# https://github.com/microsoft/pyright/blob/main/specs/dataclass_transforms.md
def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_specifiers: tuple[type | Callable[..., Any], ...] = (()),
) -> Callable[[_T], _T]:
    return lambda a: a


@__dataclass_transform__(field_specifiers=(field,))
@overload
def guiclass(
    cls: T,
    *,
    gui_name: str = "gui",
    events_namespace: str = "events",
    follow_changes: bool = True,
    **dataclass_kwargs: Any,
) -> T:
    ...


@__dataclass_transform__(field_specifiers=(field,))
@overload
def guiclass(
    cls: Literal[None] = None,
    *,
    gui_name: str = "gui",
    events_namespace: str = "events",
    follow_changes: bool = True,
    **dataclass_kwargs: Any,
) -> Callable[[T], T]:
    ...


def guiclass(
    cls: Optional[T] = None,
    *,
    gui_name: str = "gui",
    events_namespace: str = "events",
    follow_changes: bool = True,
    **dataclass_kwargs: Any,
) -> Union[T, Callable[[T], T]]:
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
        The name of the property that will return a `magicgui` widget, by default "gui"
    events_namespace : str, optional
        The name of the attribute that will be added to the class, by default "events".
        This attribute will be an instance of `psygnal.SignalGroup` that will be used
        to connect events to the class.
    follow_changes : bool, optional
        If True, changes to the dataclass instance will be reflected in the gui, and
        changes to the gui will be reflected in the dataclass instance, by default True
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
    ...     y: str = 'hi'
    ...
    ...     @button
    ...     def reset(self):
    ...         self.x = 0
    ...         self.y = 'hi'
    ...
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

        setattr(cls, gui_name, _gui_descriptor(gui_name, follow_changes=follow_changes))

        if not is_dataclass(cls):
            cls = dataclass(cls, **dataclass_kwargs)  # type: ignore
        cls = evented(cls, events_namespace=events_namespace)

        setattr(cls, _GUICLASS_FLAG, True)
        return cls

    return _deco(cls) if cls is not None else _deco


def is_guiclass(obj: object) -> TypeGuard[Guiclass]:
    """Return `True` if obj is a guiclass or an instance of a guiclass."""
    return is_dataclass(obj) and hasattr(obj, _GUICLASS_FLAG)


@overload
def button(func: F, **kwargs: Any) -> F:
    ...


@overload
def button(func: Literal[None] = None, **kwargs: Any) -> Callable[[F], F]:
    ...


def button(
    func: Optional[F] = None, **button_kwargs: Any
) -> Union[F, Callable[[F], F]]:
    """Add a method as a button to a `guiclass`, which calls the decorated method.

    Parameters
    ----------
    func : callable
        The method to decorate.  If None, returns a decorator that can be applied to a
        method.
    button_kwargs : dict, optional
        Additional keyword arguments to pass to `magicgui.widgets.PushButton`.
    """

    def _deco(func):
        button_kwargs.setdefault("label", func.__name__)
        setattr(func, _BUTTON_ATTR, button_kwargs)
        return func

    return _deco(func) if func else _deco


class _gui_descriptor:
    """Descriptor that builds a widget for a dataclass or instance."""

    def __init__(self, name: str = "", follow_changes: bool = True):
        self._name = name
        self._follow_changes = follow_changes

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner):
        wdg = build_widget(owner if instance is None else instance)

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
    signals = events.signals if isinstance(events, SignalGroup) else {}

    # in cases of classes with `__slots__`, widget.changed.connect_setattr(instance...)
    # will show a RuntimeWarning because `instance` will not be weak referenceable.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        for widget in gui:
            if isinstance(widget, ValueWidget):
                # connect changes in the widget to the instance
                if hasattr(instance, widget.name):
                    try:
                        widget.changed.connect_setattr(instance, widget.name)
                    except TypeError:
                        warnings.warn(
                            f"Could not bind {widget.name} to {instance}. "
                            "This may be because the instance has __slots__ or "
                            "other attribute restrictions. Please update psygnal."
                        )

                # connect changes from the instance to the widget
                if widget.name in signals:
                    signals[widget.name].connect_setattr(widget, "value")


def unbind_gui_from_instance(gui: ContainerWidget, instance: Any) -> None:
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
        if isinstance(widget, ValueWidget):
            widget.changed.disconnect_setattr(instance, widget.name, missing_ok=True)
