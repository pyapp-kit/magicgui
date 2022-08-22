import ipaddress
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from pydantic import BaseModel, PrivateAttr
from pydantic.fields import FieldInfo as PydanticFieldInfo
from pydantic.fields import ModelField, Undefined
from pydantic.main import ModelMetaclass

from magicgui import widgets

_T = TypeVar("_T")


class FieldInfo(PydanticFieldInfo):
    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        ...


def Field(default: Any = Undefined, **kwargs):
    field_info = FieldInfo(default, **kwargs)
    field_info._validate()
    return field_info


def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_descriptors: Tuple[Union[type, Callable[..., Any]], ...] = (()),
) -> Callable[[_T], _T]:
    return lambda a: a


@__dataclass_transform__(kw_only_default=True, field_descriptors=(Field, FieldInfo))
class GUIModelMetaclass(ModelMetaclass):
    def __new__(
        cls,
        name: str,
        bases: Tuple[Type[Any], ...],
        class_dict: Dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        new_cls = super().__new__(cls, name, bases, class_dict, **kwargs)

        widgets = {
            k: get_widget_info_for_field(v) for k, v in new_cls.__fields__.items()
        }
        cls.__widgets__ = widgets  # TODO: add to dir
        return new_cls


WidgetMeta = Tuple[Type[widgets._bases.ValueWidget], Dict[str, Any]]


def get_widget_class_for_field(field: ModelField) -> Optional[WidgetMeta]:
    if issubclass(field.type_, str):
        # if field.field_info.max_length:
        #     return AutoString(length=field.field_info.max_length)
        return widgets.LineEdit, {}
    if issubclass(field.type_, float):
        return widgets.FloatSpinBox, {}
    if issubclass(field.type_, bool):
        return widgets.CheckBox, {}
    if issubclass(field.type_, int):
        return widgets.SpinBox, {}
    if issubclass(field.type_, datetime):
        return widgets.DateTimeEdit, {}
    if issubclass(field.type_, date):
        return widgets.DateEdit, {}
    if issubclass(field.type_, timedelta):
        return widgets.TimeEdit, {}
    if issubclass(field.type_, time):
        return widgets.TimeEdit, {}
    if issubclass(field.type_, Enum):
        return widgets.ComboBox, {}
    if issubclass(field.type_, bytes):
        return widgets.LineEdit, {}
    if issubclass(field.type_, Decimal):
        # return Numeric(
        #     precision=getattr(field.type_, "max_digits", None),
        #     scale=getattr(field.type_, "decimal_places", None),
        # )
        return widgets.FloatSpinBox, {}
    if issubclass(field.type_, ipaddress.IPv4Address):
        return widgets.LineEdit, {}
    if issubclass(field.type_, ipaddress.IPv4Network):
        return widgets.LineEdit, {}
    if issubclass(field.type_, ipaddress.IPv6Address):
        return widgets.LineEdit, {}
    if issubclass(field.type_, ipaddress.IPv6Network):
        return widgets.LineEdit, {}
    if issubclass(field.type_, Path):
        # FIXME: this is really a ValueWidget
        return widgets.FileEdit, {}  # type: ignore
    if issubclass(field.type_, uuid.UUID):
        return widgets.LineEdit, {}


def get_widget_info_for_field(field: ModelField) -> Optional[WidgetMeta]:
    _wdg_kwargs = getattr(field.field_info, "widget_kwargs", Undefined)
    user_kwargs = {} if _wdg_kwargs is Undefined else _wdg_kwargs
    if not isinstance(user_kwargs, Mapping):
        raise TypeError(f"widget_kwargs must be a mapping, not {type(user_kwargs)}")

    _wdg_class = getattr(field.field_info, "widget_class", Undefined)
    if _wdg_class is not Undefined:
        if isinstance(_wdg_class, type) and issubclass(
            _wdg_class, widgets._bases.ValueWidget
        ):
            return _wdg_class, dict(user_kwargs)
        raise TypeError(f"widget_class '{_wdg_class}' is not a subclass of ValueWidget")
    meta = get_widget_class_for_field(field)
    if meta is not None:
        wdg_class, wdg_kwargs = meta
        wdg_kwargs.update(user_kwargs)
        return wdg_class, wdg_kwargs
    return None


class GUIModel(BaseModel, metaclass=GUIModelMetaclass):
    __slots__ = ("__weakref__",)
    __widgets__: Dict[str, WidgetMeta]  # move?
    _gui: Optional[widgets.Container] = PrivateAttr(None)

    @property
    def gui(self) -> widgets.Container:
        if self._gui is None:
            self._gui = type(self).build(self.dict(exclude_unset=True))
            self._connect_gui()
        return self._gui

    def _connect_gui(self) -> None:
        for widget in self._gui or ():
            if hasattr(self, widget.name):
                widget = cast(widgets._bases.ValueWidget, widget)
                widget.changed.connect_setattr(self, widget.name)

    def _disconnect_gui(self) -> Optional[widgets.Container]:
        for widget in self._gui or ():
            widget = cast(widgets._bases.ValueWidget, widget)
            widget.changed.disconnect_setattr(self, widget.name, missing_ok=True)
        if self._gui is not None:
            popped, self._gui = self._gui, None
            return popped
        return None

    @classmethod
    def build(cls, values: Union[Mapping[str, Any], None] = None) -> widgets.Container:
        if values is None:
            values = {}

        wdgs = []
        for field_name, field in cls.__fields__.items():
            meta = cls.__widgets__.get(field_name, None)
            if meta is None:
                continue
            wdg_cls, wdg_kwargs = meta
            wdg_kwargs["value"] = values.get(field_name, field.get_default())
            wdg_kwargs["name"] = field_name
            new_widget = wdg_cls(**wdg_kwargs)
            wdgs.append(new_widget)

        return widgets.Container(widgets=wdgs)

    def __setattr__(self, name: str, value: Any):
        if self._gui is not None:
            wdg = getattr(self._gui, name, None)
            if wdg is not None:
                wdg.value = value
        return super().__setattr__(name, value)


def build_widget_for_model(model: BaseModel) -> widgets.Container:
    # TODO: ... for stuff that didn't subclass on GUIModel
    ...


class T(GUIModel):
    x: int
