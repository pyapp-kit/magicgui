from dataclasses import dataclass, field
from typing import NamedTuple, Optional

import pytest
from typing_extensions import Annotated, TypedDict

from magicgui.schema._ui_field import UiField, build_widget, get_ui_fields
from magicgui.widgets import Container

EXPECTED = (
    UiField(name="a", type=int, nullable=True),
    UiField(name="b", type=str, description="the b"),
    UiField(name="c", default=0.0, type=float, widget="FloatSlider"),
)


def _assert_uifields(cls, instantiate=True):
    result = tuple(get_ui_fields(cls))
    assert result == EXPECTED
    wdg = build_widget(cls)
    assert isinstance(wdg, Container)
    assert wdg.asdict() == {
        "a": 0,
        "b": "",
        "c": 0.0,
    }
    if instantiate:
        instance = cls(a=1, b="hi")
        assert tuple(get_ui_fields(instance)) == EXPECTED
        wdg2 = build_widget(instance)
        assert isinstance(wdg2, Container)
        assert wdg2.asdict() == {
            "a": 1,
            "b": "hi",
            "c": 0.0,
        }


def test_attrs_descriptor():
    attrs = pytest.importorskip("attrs")

    @attrs.define
    class Foo:
        a: Optional[int]
        b: str = attrs.field(metadata={"description": "the b"})
        c: float = attrs.field(default=0.0, metadata={"widget": "FloatSlider"})

    _assert_uifields(Foo)


def test_dataclass():
    @dataclass
    class Foo:
        a: Optional[int]
        b: str = field(metadata={"description": "the b"})
        c: float = field(default=0.0, metadata={"widget": "FloatSlider"})

    _assert_uifields(Foo)


def test_pydantic():
    pytest.importorskip("pydantic")
    import pydantic.version
    from pydantic import BaseModel, Field

    if pydantic.version.VERSION.startswith("1"):

        class Foo(BaseModel):
            a: Optional[int]
            b: str = Field(description="the b")
            c: float = Field(0.0, widget="FloatSlider")

    else:

        class Foo(BaseModel):
            a: Optional[int]
            b: str = Field(description="the b")
            c: float = Field(0.0, json_schema_extra={"widget": "FloatSlider"})

    _assert_uifields(Foo)


def test_pydantic_dataclass():
    pydantic = pytest.importorskip("pydantic")

    @pydantic.dataclasses.dataclass
    class Foo:
        a: Optional[int]
        b: str = pydantic.Field(description="the b")
        c: float = pydantic.Field(0.0, json_schema_extra={"widget": "FloatSlider"})

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

    # instantiaed TypedDicts are plain dicts that don't remember their annotations
    _assert_uifields(Foo, instantiate=False)


def test_function():
    def foo(
        a: Optional[int],
        b: Annotated[str, UiField(description="the b")],
        c: Annotated[float, UiField(widget="FloatSlider")] = 0.0,
    ):
        ...

    # makes to sense to instantiate a function
    _assert_uifields(foo, instantiate=False)


def test_annotated():
    class Foo(NamedTuple):
        x: Annotated[float, UiField(default=1)] = 0.0

    with pytest.warns(
        UserWarning, match="Cannot set default value in both type annotation and field"
    ):
        fields = get_ui_fields(Foo)
        assert fields[0].default == 0

    class Foo2(NamedTuple):
        x: Annotated[float, UiField(name="y")] = 0.0

    with pytest.warns(
        UserWarning, match="Cannot set name in both type annotation and field"
    ):
        fields = get_ui_fields(Foo2)
        assert fields[0].name == "x"


def test_annotated_types_lib():
    pytest.importorskip("annotated_types")

    from annotated_types import Ge, Gt, Interval, Le, Len, Lt, MultipleOf, __version__

    from magicgui.schema._ui_field import _uikwargs_from_annotated_type as uikwargs

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


def test_annotated_types_lib_dataclass():
    pytest.importorskip("annotated_types")

    from annotated_types import Ge, Gt, Interval, Le, Len, Lt, MultipleOf

    @dataclass
    class Foo:
        a: Annotated[int, Ge(1)]
        b: Annotated[int, Gt(1)]
        c: Annotated[int, Le(10)]
        d: Annotated[int, Lt(10)]
        e: Annotated[int, MultipleOf(2)]
        f: Annotated[int, Interval(ge=1, le=5)]
        g: Annotated[list, Len(2, 5)]

    wdg = build_widget(Foo)
    assert wdg.a.min == 1
    assert wdg.b.min == 2
    assert wdg.c.max == 10
    assert wdg.d.max == 9
    assert wdg.e.step == 2
    assert wdg.f.min == 1
    assert wdg.f.max == 5
    # assert wdg.g.min_items == 2  # TODO
    # assert wdg.g.max_items == 5  # TODO


def test_resolved_type():
    f: UiField[int] = UiField(type=Annotated["int", UiField(minimum=0)])
    assert f.resolved_type is int

    f = UiField(type="int")
    assert f.resolved_type is int
