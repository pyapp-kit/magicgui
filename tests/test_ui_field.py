from typing import Optional, NamedTuple, TypedDict
import attrs
import pydantic
from typing_extensions import Annotated
import pytest
from magicgui._schema import UiField, iter_ui_fields

EXPECTED = (
    UiField(name="a", type=int, nullable=True),
    UiField(name="b", type=str, description="the b"),
    UiField(name="c", default=0, type=float, widget="FloatSlider"),
)


def _assert_uifields(cls, instantiate=True):
    fields = tuple(iter_ui_fields(cls))
    assert fields == EXPECTED
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
