from __future__ import annotations

from typing import TYPE_CHECKING, AbstractSet, Any, Callable, Mapping, NamedTuple, Type

from pydantic import BaseConfig, BaseModel, PrivateAttr
from pydantic.fields import FieldInfo as PydanticFieldInfo
from pydantic.fields import Undefined
from pydantic.main import ModelMetaclass, create_model

from magicgui import widgets
from magicgui.type_map import get_widget_class
from magicgui.widgets._bases import ContainerWidget, ValueWidget

if TYPE_CHECKING:
    import dataclasses
    from typing import Dict, Optional, Tuple, TypeVar, Union

    from pydantic.dataclasses import Dataclass as PydanticDataclass
    from pydantic.fields import ModelField, UndefinedType
    from pydantic.typing import NoArgAnyCallable
    from typing_extensions import Protocol

    class _DataclassParams:
        init: bool
        repr: bool
        eq: bool
        order: bool
        unsafe_hash: bool
        frozen: bool

    class PythonDataclass(Protocol):
        """Protocol for dataclasses.dataclass."""

        __dataclass_fields__: Dict[str, dataclasses.Field]
        __dataclass_params__: _DataclassParams

    SupportsPydantic = Union[
        BaseModel, Type[BaseModel], PydanticDataclass, Type[PydanticDataclass]
    ]
    SupportsDataclass = Union[PythonDataclass, Type[PythonDataclass]]
    UiWidget = Union[Type[ValueWidget], str]
    UiOptions = Mapping[str, Any]
    UiMeta = Tuple[UiWidget, UiOptions]
    ValueWidgetContainer = ContainerWidget[ValueWidget]
    GUIModelVar = TypeVar("GUIModelVar", bound="GUIModel")
    _T = TypeVar("_T")


# class BaseConfig:
#     ui_layout: Optional[str] = None


class ResolvedUIMetadata(NamedTuple):
    """Info required to create a widget for a field."""

    widget: Type[ValueWidget]
    options: Dict[str, Any]
    field_name: str


class FieldInfo(PydanticFieldInfo):
    """Captures extra information about a field.

    Added for magicgui:
    - ui_widget: the widget to use for the field.
    - ui_options: options to pass to the widget on construction.
    """

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
    """Used to provide extra information about a field.

    See docs for `pydantic.fields.Field` for details.

    Added for magicgui:
    - ui_widget: the widget to use for the field.
    - ui_options: options to pass to the widget on construction.
    """
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
    if hasattr(field_info, "validate"):
        # pydantic > 1.8
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
    """Metaclass for GUIModel.

    Just adds `__ui_info__` to the class.
    """

    def __new__(
        cls,
        name: str,
        bases: Tuple[Type[Any], ...],
        class_dict: Dict[str, Any],
        **kwargs: Any,
    ) -> Any:
        new_cls = super().__new__(cls, name, bases, class_dict, **kwargs)
        new_cls.__ui_info__ = _collect_pydantic_ui_info(new_cls)
        return new_cls


def _get_pydantic_model(obj: Any) -> Type[BaseModel]:
    """Try to find a pydantic BaseModel on the given object."""
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
    """Given an object, collect information needed to present a UI for it.

    Parameters
    ----------
    obj : Any
        The object to collect ui information for.  Could be a pydantic BaseModel or
        dataclass (type or instance).  Or a python dataclass.

    Returns
    -------
    Dict[str, ResolvedUIMetadata]
        A dictionary of field names to ui information.
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


def get_widget_info_for_field(field: ModelField) -> ResolvedUIMetadata:
    """Given a pydantic field, return the ui information for it.

    Parameters
    ----------
    field : ModelField
        The field to get ui information for.

    Returns
    -------
    Optional[ResolvedUIMetadata]
        The ui information for the field.  If there is no ui information for the field

    Raises
    ------
    TypeError
        _description_
    TypeError
        _description_
    """
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
    widget_kwargs["annotation"] = field.outer_type_
    return ResolvedUIMetadata(widget_class, dict(widget_kwargs), field.name)


class _build_descriptor(property):
    """Descriptor that knows how to build a widget for a Model.

    We use a descriptor here so we can know if we're being called on a model instance,
    in which case we use the current values, or if we're being called on a model class,
    in which case we use the default values.
    """

    # this subclasses property so as to sneak into the UNTOUCHED_TYPES
    # in ModelMetaclass.__new__. But we're not actually using the property
    def __init__(self) -> None:
        pass

    def __get__(  # type: ignore [override]
        self, instance: GUIModelVar, cls: Type[GUIModelVar]
    ) -> Callable[[], ValueWidgetContainer]:
        if instance is not None:
            values = instance.dict(exclude_unset=True)
        else:
            values = {
                k: f.get_default() for k, f in cls.__fields__.items() if not f.required
            }

        def _build() -> ValueWidgetContainer:
            wdg = _build_widget(cls.__ui_info__, values)
            if instance is not None:
                connect_model_to_gui(instance, wdg)
            return wdg

        return _build


class GUIModel(BaseModel, metaclass=GUIModelMetaclass):
    """Pydantic BaseModel subclass that offers a GUI at the `.gui` attribute."""

    __slots__ = ("__weakref__",)
    __ui_info__: Dict[str, ResolvedUIMetadata]  # move?
    _gui: Optional[ValueWidgetContainer] = PrivateAttr(None)

    build = _build_descriptor()  # function that builds the widget

    @property
    def gui(self) -> ValueWidgetContainer:
        """Return a GUI (Container widget) for the model."""
        if self._gui is None:
            self._gui = self.build()
        return self._gui

    def _disconnect_gui(self) -> Optional[ValueWidgetContainer]:
        wgd = None
        if self._gui is not None:
            wgd, self._gui = self._gui, None
            disconnect_model_to_from_gui(self, wgd)
        return wgd

    def __setattr__(self, name: str, value: Any):
        """Set an attribute on the model, as well as the GUI if it exists."""
        super().__setattr__(name, value)
        if self._gui is not None and name in self.__fields__:
            try:
                wdg = self._gui[name]
            except AttributeError:
                # no widget by that name
                return
            wdg.value = getattr(self, name)


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


def create_gui_model(
    __model_name: str,
    *,
    __config__: Optional[Type[BaseConfig]] = None,
    __base__: Union[None, Type[GUIModelVar], Tuple[Type[GUIModelVar], ...]] = None,
    __module__: str = __name__,
    __validators__: Dict[str, classmethod[Any]] = None,
    __cls_kwargs__: Dict[str, Any] = None,
    **field_definitions: Any,
) -> Type[GUIModelVar]:
    """Dynamically create a GUIModel class.

    Parameters
    ----------
    __model_name : str
        The name of the created model.
    __config__ : Optional[Type[BaseConfig]]
        The config class to use for the model.
    __base__ : Optional[Type[GUIModelVar], Tuple[Type[GUIModelVar], ...]]
        The base class(es) to use for the model. If provided, at least one of these
        should be a GUIModel subclasses.
    __module__ : str
        The module name to use for the model.
    __validators__ : Dict[str, classmethod[Any]]
        The validators to use for the model.
    __cls_kwargs__ : Dict[str, Any]
        The keyword arguments to use for the model.
    **field_definitions : Any
        fields of the model (or extra fields if a base is supplied) in the format
        `<name>=(<type>, <default default>)` or `<name>=<default value>, e.g.
        `foobar=(str, ...)` or `foobar=123`, or, for complex use-cases, in the format
        `<name>=<FieldInfo>`, e.g. `foo=Field(default_factory=datetime.utcnow,
        alias='bar')`
    """
    if __base__ is not None:
        if __config__ is not None:
            from pydantic.errors import ConfigError

            raise ConfigError(
                "to avoid confusion __config__ and __base__ " "cannot be used together"
            )
        if not isinstance(__base__, tuple):
            __base__ = (__base__,)
    else:
        __base__ = (GUIModel,)  # type: ignore

    return create_model(  # type: ignore
        __model_name=__model_name,
        __config__=__config__,
        __base__=__base__,
        __module__=__module__,
        __validators__=__validators__,
        __cls_kwargs__=__cls_kwargs__,
        **field_definitions,
    )
