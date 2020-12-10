import pytest

from magicgui import magicgui, widgets


def test_forward_refs():
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
