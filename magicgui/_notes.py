from __future__ import annotations

from dataclasses import Field
from enum import Enum
from typing import TYPE_CHECKING, Any, Mapping

from pydantic.fields import ModelField

from magicgui.widgets import Widget


class WidgetMeta:
    """Information needed to create a widget.

    Parameters
    ----------
    widget_class : Union[str, Type[Widget]]
        The class of the widget to create.
    widget_kwargs : dict
        The keyword arguments to pass to the widget constructor.
    name : str, optional
        The name of the field represented by this widget.
    is_output : bool
        If `True`, the widget is a display/output widget, and not one that collects
        input. By default, `False`.
    """

    __slots__ = (
        "_widget_class",
        "widget_kwargs",
        "",
        "_resolved_class",
        "name",
        "is_output",
    )
    _resolved_class: type[Widget]

    def __init__(
        self,
        widget_class: str | type[Widget],
        widget_kwargs: dict,
        name: str = "",
        is_output: bool = False,
    ) -> None:
        self._widget_class = widget_class
        self.widget_kwargs = widget_kwargs  # TODO: apply typing validators
        self.name = name
        self.is_output = is_output

    def _validate(self) -> None:
        # TODO
        # resolve widget class and check if kwargs are for the widget class
        _ = self.widget_class

    @property
    def widget_class(self) -> type[Widget]:
        """Resolved widget type, (even if originally provided as a string)."""
        if self._resolved_class is None:
            if isinstance(self._widget_class, Widget):
                self._resolved_class = self._widget_class
            else:
                self._resolved_class = _resolve_widget_class(self._widget_class)

        return self._resolved_class

    def build(self) -> Widget:
        """Create and return a widget instance."""
        return self.widget_class(**self.widget_kwargs)


def _resolve_widget_class(class_name: str) -> type[Widget]:
    """Import and type validate a widget class with the given name."""
    import importlib

    # import from magicgui widgets if not explicitly namespaced
    if "." not in class_name:
        class_name = f"magicgui.widgets.{class_name}"

    mod_name, name = class_name.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    wdg_type = getattr(mod, name)
    if not isinstance(wdg_type, type) and issubclass(wdg_type, Widget):
        raise TypeError(f"{class_name} is not a Widget subclass")
    return wdg_type


def _dataclass_field_to_ui_meta(field: Field) -> WidgetMeta:
    ...


def _pydantic_field_to_ui_meta(field: ModelField) -> WidgetMeta:
    ...


if TYPE_CHECKING:
    from typing import Callable, Protocol

    class Attribute(Protocol):
        """attrs._make.Attribute ... which doesn't appear to be type annotated."""

        name: str
        default: Any  # could be NOTHING, or Factory, then it's default_factory
        validator: Callable | list[Callable]
        repr: bool | Callable
        eq: bool | Callable
        eq_key: Callable | None
        order_key: Callable | None
        order: bool | None
        hash: bool | None
        init: bool
        metadata: Mapping
        type: Any
        converter: Callable  # convert attribute’s value to the desired format
        kw_only: bool
        inherited: bool
        on_setattr: Callable | list[Callable]


def _attrs_attribute_to_ui_meta(attr: Attribute) -> WidgetMeta:
    return WidgetMeta(attr.type, attr.kwargs)


from typing import Any, Mapping

from ._notes import WidgetMeta


# TODO: test that we're hitting the kwargs of every widget in widgets.
class WidgetOptions:
    widget_type: str | None = None
    name: str | None = None
    annotation: Any | None = None
    label: str | None = None
    tooltip: str | None = None
    visible: bool | None = None
    enabled: bool | None = None
    gui_only: bool | None = None
    backend_kwargs: bool | None = None
    value: Any = None  # should be default
    bind: Callable | Any | None = None
    nullable: bool | None = None
    text: str | None = None
    choices: list | Callable | Enum = None
    allow_multiple: bool | None = None
    scrollable: bool | None = None
    labels: bool | None = None
    mode: str | None = None  # file dialog mode
    filter: str | None = None  # file dialog
    min: float | None = None
    max: float | None = None
    step: float | None = None
    orientation: str | None = None
    readout: bool | None = None
    tracking: bool | None = None
    min_pos: float | None = None
    max_pos: float | None = None
    base: float | None = None
    start: int | None = None
    stop: int | None = None
    function: Callable | None = None
    call_button: bool | str | None = None


class ContainerOptions:
    layout: str | None = None
    persist: bool | None = None
    tooltips: bool | None = None
    auto_call: bool | None = None
    result_widget: bool | None = None


def prepare_widget(
    type: Any = Undefined,
    default: Any = Undefined,
    *,
    ui_options: Mapping[str, Any] | None = None,
    name: str = "",
    is_output: bool = False,
) -> WidgetMeta:
    """Prepare widget type and options for a given field."""
