import ipaddress
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Sequence,
    AbstractSet,
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

from pydantic import BaseModel, PrivateAttr, BaseConfig
from pydantic.fields import FieldInfo as PydanticFieldInfo
from pydantic.fields import ModelField, Undefined, UndefinedType
from pydantic.main import ModelMetaclass
from pydantic.typing import NoArgAnyCallable
from magicgui import widgets

_T = TypeVar("_T")


# class BaseConfig:
#     ui_layout: Optional[str] = None


class FieldInfo(PydanticFieldInfo):
    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        ui_widget = kwargs.pop("ui_widget", Undefined)
        ui_options = kwargs.pop("ui_options", Undefined)
        super().__init__(default=default, **kwargs)
        self.ui_widget = ui_widget
        self.ui_options = ui_options


UiWidget = Union[Type[widgets._bases.ValueWidget], str]
UiOptions = Mapping[str, Any]
UiMeta = Tuple[UiWidget, UiOptions]


def Field(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    exclude: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    include: Union[
        AbstractSet[Union[int, str]], Mapping[Union[int, str], Any], Any
    ] = None,
    const: Optional[bool] = None,
    gt: Optional[float] = None,
    ge: Optional[float] = None,
    lt: Optional[float] = None,
    le: Optional[float] = None,
    multiple_of: Optional[float] = None,
    max_digits: Optional[int] = None,
    decimal_places: Optional[int] = None,
    min_items: Optional[int] = None,
    max_items: Optional[int] = None,
    unique_items: bool = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allow_mutation: bool = True,
    regex: Optional[str] = None,
    discriminator: str = None,
    repr: bool = True,
    ui_widget: Union[UiWidget, UndefinedType] = Undefined,
    ui_options: Union[UiOptions, UndefinedType] = Undefined,
    **extra: Any,
) -> Any:
    field_info = FieldInfo(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        exclude=exclude,
        include=include,
        const=const,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        multiple_of=multiple_of,
        max_digits=max_digits,
        decimal_places=decimal_places,
        min_items=min_items,
        max_items=max_items,
        unique_items=unique_items,
        min_length=min_length,
        max_length=max_length,
        allow_mutation=allow_mutation,
        regex=regex,
        discriminator=discriminator,
        repr=repr,
        ui_widget=ui_widget,
        ui_options=ui_options,
        **extra,
    )
    field_info._validate()
    return field_info


def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_specifiers: Tuple[Union[type, Callable[..., Any]], ...] = (()),
) -> Callable[[_T], _T]:
    return lambda a: a


@__dataclass_transform__(kw_only_default=True, field_specifiers=(Field, FieldInfo))
class GUIModelMetaclass(ModelMetaclass):
    def __new__(
        cls,
        name: str,
        bases: Tuple[Type[Any], ...],
        class_dict: Dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        new_cls = super().__new__(cls, name, bases, class_dict, **kwargs)

        # TODO: add to dir
        cls.__widgets__ = {
            k: get_widget_info_for_field(v) for k, v in new_cls.__fields__.items()
        }
        return new_cls


def get_widget_class_for_field(field: ModelField) -> Optional[UiMeta]:
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


def get_widget_info_for_field(field: ModelField) -> Optional[UiMeta]:
    _wdg_kwargs = getattr(field.field_info, "widget_kwargs", Undefined)
    user_kwargs = {} if _wdg_kwargs is Undefined else _wdg_kwargs
    if not isinstance(user_kwargs, Mapping):
        raise TypeError(f"widget_kwargs must be a mapping, not {type(user_kwargs)}")

    _wdg_class = getattr(field.field_info, "ui_widget", Undefined)
    if _wdg_class is not Undefined:
        _wdg_class = cast(UiWidget, _wdg_class)
        if isinstance(_wdg_class, type) and issubclass(
            _wdg_class, widgets._bases.ValueWidget
        ):
            return _wdg_class, dict(user_kwargs)
        elif isinstance(_wdg_class, str):
            raise NotImplementedError(
                "Passing widget class as string is not yet supported"
            )
        raise TypeError(f"ui_widget '{_wdg_class}' is not a subclass of ValueWidget")
    meta = get_widget_class_for_field(field)
    if meta is not None:
        wdg_class, wdg_kwargs = meta
        cast(dict, wdg_kwargs).update(user_kwargs)
        # TODO: convert string to class
        return wdg_class, wdg_kwargs
    return None

class GUIModel(BaseModel, metaclass=GUIModelMetaclass):
    __slots__ = ("__weakref__",)
    __widgets__: Dict[str, UiMeta]  # move?
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
            wdg_kwargs = dict(wdg_kwargs)
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
