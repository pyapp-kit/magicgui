from enum import Enum
from typing import Optional, Union

import pytest

from magicgui import magicgui, register_type, type_map, types, widgets
from magicgui._type_resolution import resolve_single_type


def test_forward_refs():
    """Test that forward refs parameter annotations get resolved."""

    @magicgui
    def testA(x: "tests.MyInt" = "1"):  # type: ignore  # noqa
        pass

    @magicgui
    def testB(x="1"):
        pass

    # because tests.MyInt is a subclass of int, it will be shown as a SpinBox
    assert isinstance(testA.x, widgets.SpinBox)
    # whereas without the forward ref type annotation, it would have been a LineEdit
    assert isinstance(testB.x, widgets.LineEdit)

    with pytest.raises(ImportError) as err:
        # bad forward ref
        @magicgui
        def testA(x: "testsd.MyInt" = "1"):  # type: ignore  # noqa
            pass

    assert "Magicgui could not resolve ForwardRef" in str(err.value)


@pytest.mark.parametrize(
    "cls, string", [("LineEdit", "str"), ("SpinBox", "int"), ("FloatSpinBox", "float")]
)
def test_pick_widget_builtins_forward_refs(cls, string):
    wdg = type_map.pick_widget_type(annotation=string)[0]
    assert getattr(wdg, "__name__") == cls


def test_forward_refs_return_annotation():
    """Test that forward refs return annotations get resolved."""

    @magicgui
    def testA() -> int:
        return 1

    @magicgui
    def testB() -> "tests.MyInt":  # type: ignore  # noqa
        return 1

    from tests import MyInt

    results = []
    register_type(MyInt, return_callback=lambda *x: results.append(x))

    testA()
    assert not results

    testB()
    gui, result, return_annotation = results[0]
    assert isinstance(gui, widgets.FunctionGui)
    assert result == 1
    # the forward ref has been resolved
    assert return_annotation is MyInt


def test_pathlike_annotation():
    import pathlib

    @magicgui(fn={"mode": "r"})
    def widget(fn: types.PathLike):
        print(fn)

    assert isinstance(widget.fn, widgets.FileEdit)
    assert widget.fn.mode is types.FileDialogMode.EXISTING_FILE

    # an equivalent union also works
    @magicgui(fn={"mode": "rm"})
    def widget2(fn: Union[bytes, pathlib.Path, str]):
        print(fn)

    assert isinstance(widget2.fn, widgets.FileEdit)
    assert widget2.fn.mode is types.FileDialogMode.EXISTING_FILES


def test_optional_type():
    @magicgui(x=dict(choices=["a", "b"]))
    def widget(x: Optional[str] = None):
        ...

    assert isinstance(widget.x, widgets.ComboBox)
    assert widget.x.value is None
    assert None in widget.x.choices


def test_widget_options():
    """Test bugfix: widget options shouldn't persist to next widget."""
    E = Enum("E", ["a", "b", "c"])
    choice1 = widgets.create_widget(annotation=E)
    choice2 = widgets.create_widget(annotation=Optional[E])
    choice3 = widgets.create_widget(annotation=E)
    assert choice1._nullable is choice3._nullable is False
    assert choice2._nullable is True


def test_nested_forward_refs():

    resolved = resolve_single_type(Optional['List["numpy.ndarray"]'])  # noqa

    from typing import List

    import numpy as np

    assert resolved == Optional[List[np.ndarray]]
