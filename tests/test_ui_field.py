from typing import NamedTuple, Optional

import attrs
import pydantic
import pytest
from typing_extensions import Annotated, TypedDict

from magicgui._schema import UiField, _build_widget, iter_ui_fields

EXPECTED = (
    UiField(name="a", type=int, nullable=True),
    UiField(name="b", type=str, description="the b"),
    UiField(name="c", default=0, type=float, widget="FloatSlider"),
)


def _assert_uifields(cls, instantiate=True):
    fields = tuple(iter_ui_fields(cls))
    assert fields == EXPECTED
    _build_widget(fields)
    if instantiate:
        fields2 = tuple(iter_ui_fields(cls(a=1, b="hi")))
        assert fields2 == EXPECTED


def test_attrs_descriptor():
    @attrs.define
    class Foo:
        a: Optional[int]
        b: str = attrs.field(metadata={"description": "the b"})
        c: float = attrs.field(default=0.0, metadata={"widget": "FloatSlider"})

    _assert_uifields(Foo)


def test_dataclass():
    from dataclasses import dataclass, field

    @dataclass
    class Foo:
        a: Optional[int]
        b: str = field(metadata={"description": "the b"})
        c: float = field(default=0.0, metadata={"widget": "FloatSlider"})

    _assert_uifields(Foo)


def test_pydantic():
    class Foo(pydantic.BaseModel):
        a: Optional[int]
        b: str = pydantic.Field(description="the b")
        c: float = pydantic.Field(0, widget="FloatSlider")

    _assert_uifields(Foo)


def test_pydantic_dataclass():
    @pydantic.dataclasses.dataclass
    class Foo:
        a: Optional[int]
        b: str = pydantic.Field(description="the b")
        c: float = pydantic.Field(0, widget="FloatSlider")

    _assert_uifields(Foo)


def test_named_tuple():
    class Foo(NamedTuple):
        a: Optional[int]
        b: Annotated[str, UiField(description="the b")]
        c: Annotated[float, UiField(widget="FloatSlider")] = 0.0

    _assert_uifields(Foo)


def test_typed_dict():
    class Foo(TypedDict):
        a: Optional[int]
        b: Annotated[str, UiField(description="the b")]
        c: Annotated[float, UiField(default=0.0, widget="FloatSlider")]

    _assert_uifields(Foo, instantiate=False)


def test_function():
    def foo(
        a: Optional[int],
        b: Annotated[str, UiField(description="the b")],
        c: Annotated[float, UiField(widget="FloatSlider")] = 0.0,
    ):
        ...

    _assert_uifields(foo, instantiate=False)


def test_annotated():
    class Foo(NamedTuple):
        x: Annotated[float, UiField(default=1)] = 0.0

    with pytest.warns(
        UserWarning, match="Cannot set default value in both type annotation and field"
    ):
        fields = tuple(iter_ui_fields(Foo))
        assert fields[0].default == 0

    class Foo2(NamedTuple):
        x: Annotated[float, UiField(name="y")] = 0.0

    with pytest.warns(
        UserWarning, match="Cannot set name in both type annotation and field"
    ):
        fields = tuple(iter_ui_fields(Foo2))
        assert fields[0].name == "x"


def test_annotated_types_lib():
    from annotated_types import Ge, Gt, Interval, Le, Len, Lt, MultipleOf, __version__

    from magicgui._schema import _uikwargs_from_annotated_type as uikwargs

    at_ver = tuple(int(v) for v in __version__.split("."))

    def assert_eq(annotated_type, expected):
        result = uikwargs(annotated_type)
        assert result.pop("type") == int
        result.pop("_original_annotation")
        assert result == expected

    assert_eq(Annotated[int, Ge(0)], {"minimum": 0})
    assert_eq(Annotated[int, Gt(0)], {"exclusive_minimum": 0})
    assert_eq(Annotated[int, Le(0)], {"maximum": 0})
    assert_eq(Annotated[int, Lt(0)], {"exclusive_maximum": 0})
    L = Len(2, max_exclusive=5) if at_ver < (0, 4) else Len(2, max_length=4)
    assert_eq(Annotated[int, L], {"min_items": 2, "max_items": 4})
    assert_eq(Annotated[int, MultipleOf(2)], {"multiple_of": 2})
    assert_eq(
        Annotated[int, Interval(gt=0, lt=2)],
        {"exclusive_minimum": 0, "exclusive_maximum": 2},
    )
    assert_eq(Annotated[int, Interval(ge=1, le=3)], {"minimum": 1, "maximum": 3})

    if at_ver >= (0, 4):
        from annotated_types import MaxLen, MinLen

        assert_eq(Annotated[int, MinLen(2)], {"min_items": 2})
        assert_eq(Annotated[int, MaxLen(4)], {"max_items": 4})


def test_resolved_type():
    f = UiField(type=Annotated["int", UiField(minimum=0)])
    assert f.resolved_type is int

    f = UiField(type="int")
    assert f.resolved_type is int