from typing import Optional, Union

import pytest

from magicgui import magicgui, register_type, types, widgets


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

    assert "Could not resolve the magicgui forward reference" in str(err.value)


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
