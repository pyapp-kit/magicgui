from dataclasses import dataclass
from typing import Any, Callable, Literal, Optional, Type, TypeVar, Union, overload

from psygnal import SignalGroup, evented

from magicgui._ui_field import build_widget
from magicgui.widgets import PushButton
from magicgui.widgets._bases import ContainerWidget, ValueWidget

T = TypeVar("T", bound=Type[Any])
F = TypeVar("F", bound=Callable)

_BUTTON_ATTR = "_magicgui_button"


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
                _bind_gui_changes_to_instance(wdg, instance)
            # cache it on the instance
            # call del instance.<_name> to remove it
            setattr(instance, self._name, wdg)
        return wdg


def _bind_gui_changes_to_instance(
    gui: ContainerWidget, instance: Any, two_way: bool = True
) -> None:
    """Set change events in `gui` to update the corresponding attributes in `model`."""
    events = getattr(instance, "events", None) if two_way else None
    signals = events.signals if isinstance(events, SignalGroup) else {}
    for widget in gui:
        if isinstance(widget, ValueWidget):
            if hasattr(instance, widget.name):
                widget.changed.connect_setattr(instance, widget.name)
            if widget.name in signals:
                signals[widget.name].connect_setattr(widget, "value")


def guiclass(
    cls: T,
    *,
    gui_name: str = "gui",
    events_namespace: str = "events",
    follow_changes: bool = True,
    **dataclass_kwargs: Any,
) -> T:
    """Turn class into a dataclass with a property (`gui_name`) that returns a gui."""
    cls = dataclass(cls, **dataclass_kwargs)  # type: ignore
    cls = evented(cls, events_namespace=events_namespace)
    setattr(cls, gui_name, _gui_descriptor(gui_name, follow_changes=follow_changes))
    return cls


@overload
def button(func: F, **kwargs: Any) -> F:
    ...


@overload
def button(func: Literal[None] = None, **kwargs: Any) -> Callable[[F], F]:
    ...


def button(
    func: Optional[F] = None, **button_kwargs: Any
) -> Union[F, Callable[[F], F]]:
    """Decorate a method as a button."""

    def _deco(func):
        button_kwargs.setdefault("label", func.__name__)
        setattr(func, _BUTTON_ATTR, button_kwargs)
        return func

    return _deco(func) if func else _deco
