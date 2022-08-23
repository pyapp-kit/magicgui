from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    Dict,
    Mapping,
    NamedTuple,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel, PrivateAttr
from pydantic.fields import FieldInfo as PydanticFieldInfo
from pydantic.fields import ModelField, Undefined, UndefinedType
from pydantic.main import ModelMetaclass

from magicgui import widgets
from magicgui.type_map import get_widget_class
from magicgui.types import WidgetOptions
from magicgui.widgets._bases import ContainerWidget, ValueWidget

if TYPE_CHECKING:
    import dataclasses

    from pydantic.dataclasses import Dataclass as PydanticDataclass
    from pydantic.typing import NoArgAnyCallable

    class _DataclassParams:
        init: bool
        repr: bool
        eq: bool
        order: bool
        unsafe_hash: bool
        frozen: bool

    class PythonDataclass(Protocol):
        __dataclass_fields__: Dict[str, dataclasses.Field]
        __dataclass_params__: _DataclassParams

    SupportsPydantic = Union[
        BaseModel, Type[BaseModel], PydanticDataclass, Type[PydanticDataclass]
    ]
    SupportsDataclass = Union[PythonDataclass, Type[PythonDataclass]]
    UiWidget = Union[Type[ValueWidget], str]
    UiOptions = Mapping[str, Any]
    UiMeta = Tuple[UiWidget, UiOptions]


_T = TypeVar("_T")

# class BaseConfig:
#     ui_layout: Optional[str] = None


class ResolvedUIMetadata(NamedTuple):
    widget: Type[ValueWidget]
    options: WidgetOptions
    field_name: str


class FieldInfo(PydanticFieldInfo):
    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        ui_widget = kwargs.pop("ui_widget", Undefined)
        ui_options = kwargs.pop("ui_options", Undefined)
        super().__init__(default=default, **kwargs)
        self.ui_widget = ui_widget
        self.ui_options = ui_options


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


# https://peps.python.org/pep-0681/
# https://github.com/microsoft/pyright/blob/main/specs/dataclass_transforms.md
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
        cls.__ui_info__ = _collect_pydantic_ui_info(new_cls)
        return new_cls


def _get_pydantic_model(obj: Any) -> Type[BaseModel]:
    if isinstance(obj, BaseModel):
        model_cls = type(obj)
    elif hasattr(obj, "__pydantic_model__"):
        model_cls = obj.__pydantic_model__
    else:
        model_cls = obj

    if not issubclass(model_cls, BaseModel):
        raise TypeError(f"{model_cls} must be either BaseModel or dataclass")
    return model_cls


def collect_ui_info(
    obj: Union[SupportsPydantic, PythonDataclass, Type[PythonDataclass]],
) -> Dict[str, ResolvedUIMetadata]:
    """Given an object, collect ui information.

    Parameters
    ----------
    obj : Any
        The object to collect ui information for.  Could be a pydantic BaseModel or
        dataclass (type or instance).  Or a python dataclass.
    """
    try:
        model = _get_pydantic_model(obj)
    except TypeError:
        pass
    else:
        return _collect_pydantic_ui_info(model)

    if hasattr(obj, "__dataclass_fields__") and hasattr(obj, "__dataclass_params__"):
        # TODO:
        ...
    raise TypeError(f"Cannot collect UI information for type {type(obj)}")


def _collect_pydantic_ui_info(model: Type[BaseModel]) -> Dict[str, ResolvedUIMetadata]:
    ui_info = {}
    for field_name, field_info in model.__fields__.items():
        info = get_widget_info_for_field(field_info)
        if info is not None:
            ui_info[field_name] = info
    return ui_info


def get_widget_info_for_field(field: ModelField) -> Optional[ResolvedUIMetadata]:
    # search for user provided ui_options in field_info
    _ui_opts = getattr(field.field_info, "ui_options", Undefined)
    user_options = {} if _ui_opts is Undefined else _ui_opts
    if not isinstance(user_options, Mapping):
        raise TypeError(f"ui_options must be a mapping, not {type(user_options)}")
    user_options = dict(user_options)

    _ui_wdg = getattr(field.field_info, "ui_widget", Undefined)
    if _ui_wdg is not Undefined:
        if not isinstance(_ui_wdg, str) or (
            isinstance(_ui_wdg, type) and issubclass(_ui_wdg, ValueWidget)
        ):
            raise TypeError(
                "ui_widget must be a string, or subclass of ValueWidget, "
                f"not {type(_ui_wdg)}"
            )
        user_options["widget_type"] = _ui_wdg

    widget_class, widget_kwargs = get_widget_class(
        annotation=field, options=user_options, is_result=False
    )
    return ResolvedUIMetadata(widget_class, widget_kwargs, field.name)


ValueWidgetContainer = ContainerWidget[ValueWidget]


class GUIModel(BaseModel, metaclass=GUIModelMetaclass):
    __slots__ = ("__weakref__",)
    __ui_info__: Dict[str, ResolvedUIMetadata]  # move?
    _gui: Optional[ValueWidgetContainer] = PrivateAttr(None)

    @property
    def gui(self) -> ValueWidgetContainer:
        if self._gui is None:
            self._gui = type(self).build(self.dict(exclude_unset=True))
            connect_model_to_gui(self, self._gui)
        return self._gui

    def _disconnect_gui(self) -> Optional[ValueWidgetContainer]:
        wgd = None
        if self._gui is not None:
            wgd, self._gui = self._gui, None
            disconnect_model_to_from_gui(self, wgd)
        return wgd

    def __setattr__(self, name: str, value: Any):
        if self._gui is not None:
            wdg = getattr(self._gui, name, None)
            if wdg is not None:
                wdg.value = value
        return super().__setattr__(name, value)

    @classmethod
    def build(
        cls, values: Union[Mapping[str, Any], None] = None
    ) -> ValueWidgetContainer:
        values = dict(values) if values else {}
        for field_name, field in cls.__fields__.items():
            values.setdefault(field_name, field.get_default())
        return _build_widget(cls.__ui_info__, values)


def connect_model_to_gui(model: GUIModel, gui: ValueWidgetContainer) -> None:
    for widget in gui:
        if hasattr(model, widget.name):
            widget.changed.connect_setattr(model, widget.name)


def disconnect_model_to_from_gui(model: GUIModel, gui: ValueWidgetContainer) -> None:
    for widget in gui:
        widget.changed.disconnect_setattr(model, widget.name, missing_ok=True)


def _build_widget(
    ui_info: Dict[str, ResolvedUIMetadata],
    values: Union[Mapping[str, Any], None] = None,
) -> ValueWidgetContainer:
    if values is None:
        values = {}

    wdgs = []
    for field_name, ui_metadata in ui_info.items():
        wdg_kwargs = dict(ui_metadata.options)
        wdg_kwargs.setdefault("name", field_name)
        value = values.get(field_name, Undefined)
        if value is not Undefined:
            wdg_kwargs["value"] = value
        new_widget = ui_metadata.widget(**wdg_kwargs)
        wdgs.append(new_widget)

    return widgets.Container(widgets=wdgs)