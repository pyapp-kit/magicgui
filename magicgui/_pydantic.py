from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel, fields
from pydantic.typing import is_callable_type
from pydantic.utils import get_model
from typing_extensions import Literal

from magicgui import create_widget, magicgui, widgets
from magicgui.types import WidgetOptionKeys, WidgetOptions, _is_option_key
from magicgui.widgets._bases.value_widget import UNSET


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


# TODO: some of this should probably live in type_map instead
def model_field_widget(field: fields.ModelField) -> widgets.Widget | None:
    """Create widget for pydantic model field."""
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


def _subfield_container(sub_fields, **container_kwargs):
    return widgets.Container(
        widgets=filter(None, (model_field_widget(sf) for sf in sub_fields)),
        labels=False,
        layout="horizontal",
        **container_kwargs,
    )


def _field_singleton_sub_fields_widget(fields: list[fields.ModelField], **kwargs):
    return _subfield_container(fields, **kwargs)  # FIXME: not correct for lists
