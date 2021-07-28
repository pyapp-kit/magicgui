from typing import Any, List, Literal, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, Field
from pydantic.fields import ModelField

from magicgui import widgets


class S(BaseModel):
    x: int = 1


class T(BaseModel):
    integer: int = 0
    string: str = "str"
    int_list: List[int] = [1]
    tup_int_str: Tuple[int, str, float] = [1, "sr", 12.0]
    tup_int_var: Tuple[int, ...] = (1, 2, 3)
    u_lit: Union[Literal["a"], Literal["b"]] = "a"
    int_or_str: Union[int, str] = "a"
    s: S = S()

    class Config:
        validate_assignment = True


# print([f.type_ for f in T.__fields__.values()])

# q = ModelField(
#     name="u_lit",
#     type_=Union[Literal["a"], Literal["b"]],
#     required=True,
#     class_validators={},
#     model_config=BaseConfig,
# )

from pydantic import fields
from pydantic.typing import is_callable_type
from pydantic.utils import get_model
from qtpy.QtWidgets import QFormLayout, QWidget

SEQUENCE_SHAPES = {
    fields.SHAPE_LIST,
    fields.SHAPE_TUPLE_ELLIPSIS,
    fields.SHAPE_SEQUENCE,
    fields.SHAPE_SET,
    fields.SHAPE_FROZENSET,
    fields.SHAPE_ITERABLE,
}


def model_widget(model: Union[Type["BaseModel"], Type["Dataclass"]]) -> QWidget:
    model = get_model(model)

    widget = widgets.Container(labels=True)
    for name, field in model.__fields__.items():
        display_name = field.field_info.title or name
        sub_widget = field_widget(field)
        if sub_widget:
            sub_widget.name = name
            widget.append(sub_widget)
        else:
            print(name, field.type_)
    return widget


# see `schema.field_type_schema`
def field_widget(field: ModelField) -> QWidget:
    if field.shape in SEQUENCE_SHAPES:
        # type: array
        widget = _field_singleton_widget(field)
    elif field.shape in fields.MAPPING_LIKE_SHAPES:
        # type: object
        widget = _field_singleton_widget(field)
    elif field.shape == fields.SHAPE_TUPLE:
        # type: array of known length
        widget = widgets.Container(
            widgets=[field_widget(sf) for sf in field.sub_fields],
            labels=True,
            layout="horizontal",
        )
    else:
        assert field.shape in {
            fields.SHAPE_SINGLETON,
            fields.SHAPE_GENERIC,
        }, field.shape
        widget = _field_singleton_widget(field)
    return widget


def _field_singleton_widget(field: ModelField):
    if field.sub_fields:
        return _field_singleton_sub_fields_widget(field.sub_fields)
    if field.type_ is Any or field.type_.__class__ == TypeVar:
        # return {}, definitions, nested_models  # no restrictions
        pass
    if field.type_ in {None, type(None), Literal[None]}:
        # return {'type': 'null'}, definitions, nested_models
        pass
    if is_callable_type(field.type_):
        pass
    if field.field_info is not None and field.field_info.const:
        pass
        # make it a QLabel
    if issubclass(field.type_, int):
        return widgets.SpinBox()
    if issubclass(field.type_, float):
        return widgets.FloatSpinBox()
    if issubclass(field.type_, str):
        return widgets.LineEdit()
    if issubclass(field.type_, BaseModel):
        return model_widget(field.type_)


def _field_singleton_sub_fields_widget(fields: List[ModelField]):
    pass


model_widget(T).show(run=True)
