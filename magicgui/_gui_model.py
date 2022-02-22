from __future__ import annotations

from typing import Any, TypeVar

from psygnal import Signal, SignalGroup, SignalInstance
from pydantic import BaseModel, PrivateAttr, fields
from pydantic.typing import is_callable_type
from pydantic.utils import get_model
from typing_extensions import Literal

from magicgui.types import WidgetOptionKeys, WidgetOptions, _is_option_key
from magicgui.widgets._bases.value_widget import UNSET

from . import widgets


def model_widget(model: type[BaseModel], **container_kwargs):
    """Create widget from Pydantic model."""
    m = get_model(model)
    return widgets.Container(
        widgets=filter(None, (model_field_widget(f) for f in m.__fields__.values())),
        **container_kwargs,
    )


_CONSTRAINT_MAP: dict[str, WidgetOptionKeys] = {
    "gt": "min",  # TODO: implement exclusive min/max
    "lt": "max",  # TODO: implement exclusive min/max
    "ge": "min",
    "le": "max",
    "multiple_of": "step",
    # not yet implemented
    # 'min_length': None,
    # 'max_length': None,
    # 'regex': None,
    # 'min_items': None,
    # 'max_items': None,
    # 'allow_mutation': True,
}


def _subfield_container(sub_fields, **container_kwargs):
    return widgets.Container(
        widgets=filter(None, (model_field_widget(sf) for sf in sub_fields)),
        labels=False,
        layout="horizontal",
        **container_kwargs,
    )


def _field_singleton_sub_fields_widget(fields: list[fields.ModelField], **kwargs):
    return _subfield_container(fields, **kwargs)  # FIXME: not correct for lists


# TODO: some of this should probably live in type_map instead
def model_field_widget(field: fields.ModelField) -> widgets.Widget | None:
    """Create widget for pydantic model field."""
    from magicgui import magicgui
    from magicgui.widgets import create_widget

    if field.shape == fields.SHAPE_TUPLE:
        return _subfield_container(field.sub_fields, name=field.name)
    if isinstance(field.type_, type) and issubclass(field.type_, BaseModel):
        return model_widget(field.type_, name=field.name)
    if field.sub_fields:
        return _field_singleton_sub_fields_widget(field.sub_fields, name=field.name)

    if field.type_ is Any or field.type_.__class__ == TypeVar:
        return None
    if field.type_ in {None, type(None), Literal[None]}:
        return None
    if is_callable_type(field.type_):
        default = field.get_default()
        if default is not None:
            return magicgui(field.get_default())
        return None

    options: WidgetOptions = {"nullable": field.allow_none}
    if field.field_info is not None:
        for c in field.field_info.get_constraints():
            if c in _CONSTRAINT_MAP:
                options[_CONSTRAINT_MAP[c]] = getattr(field.field_info, c)
        if field.field_info.const:
            options["bind"] = field.get_default()
        if field.field_info.description:
            options["tooltip"] = field.field_info.description

        for key, value in field.field_info.extra.items():
            if key.startswith("ui_"):
                _key = key[3:]
                if _is_option_key(_key):
                    options[_key] = value

        # choices: ChoicesType, enum?, Union Literal?
    value = field.get_default()
    if value is None and field.required:
        value = UNSET

    return create_widget(
        value=value,
        annotation=field.type_,
        name=field.name,
        label=field.field_info.title,
        options=options,
    )


def _build_signal_group(model: BaseModel | type[BaseModel]) -> type[SignalGroup]:
    return type(
        "Events",
        (SignalGroup,),
        {k: Signal(name=k) for k in model.__fields__},
    )


def _build_widget(instance: BaseModel, connect: bool = True) -> widgets.Container:
    cls = type(instance)
    container_kwargs = {}
    if hasattr(instance.__config__, "layout"):
        container_kwargs["layout"] = instance.__config__.layout
    if hasattr(instance.__config__, "labels"):
        container_kwargs["labels"] = instance.__config__.labels

    widget = model_widget(cls, **container_kwargs)
    for n in cls.__fields__:
        subwdg = getattr(widget, n)
        siginst = getattr(subwdg, "changed", None)
        if isinstance(siginst, SignalInstance):
            siginst.connect_setattr(instance, n)
    return widget


class GUIModel(BaseModel):
    _widget: widgets.Container = PrivateAttr(...)
    _events: SignalGroup = PrivateAttr(...)
    __slots__ = {"__weakref__"}

    def __init__(__guiself__, **data) -> None:
        super().__init__(**data)
        __guiself__._widget = _build_widget(__guiself__, __guiself__.__config__)
        __guiself__._events = _build_signal_group(__guiself__)(instance=__guiself__)

    @property
    def events(self) -> SignalGroup:
        return self._events

    @property
    def gui(self) -> widgets.Container:
        return self._widget

    def __setattr__(self, name, value):
        before = getattr(self, name, "__unset__")
        super().__setattr__(name, value)
        after = getattr(self, name, "__unset__")
        if before is not after:
            wdg = getattr(self.gui, name, None)
            if wdg is not None:
                wdg.value = after
            attr = getattr(self.events, name, None)
            if attr is not None:
                attr.emit(after)
