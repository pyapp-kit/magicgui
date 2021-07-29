import pytest

from magicgui import magic_factory
from magicgui._magicgui import MagicFactory
from magicgui.widgets import ComboBox, FunctionGui, Slider


def test_magic_factory():
    """Test basic magic_factory behavior."""

    @magic_factory(call_button=True)
    def factory(x: int = 1):
        return x

    assert isinstance(factory, MagicFactory)

    # factories make widgets that are FunctionGui instances
    widget1 = factory()
    assert isinstance(widget1, FunctionGui)
    assert widget1._call_button

    # You can call them repeatedly, and even override the initial kwargs
    # given to magic_factory (just like with functools.partial)
    widget2 = factory(call_button=False, x={"widget_type": "Slider"})
    assert widget1 is not widget2
    assert isinstance(widget2, FunctionGui)
    assert not widget2._call_button
    assert isinstance(widget2.x, Slider)

    # the widget, (like all FunctionGuis) is still callable and accepts args
    assert widget1() == 1
    assert widget1(3) == 3


def test_magic_factory_reuse():
    """Test magic_factory can be reused."""

    @magic_factory(x={"choices": ["a", "b"]})
    def factory(x="a"):
        return x

    # there was an earlier bug that overrode widget parameters.  this tests for that
    widget_a = factory()
    assert isinstance(widget_a.x, ComboBox)

    widget_b = factory()
    assert isinstance(widget_b.x, ComboBox)


def test_magic_factory_repr():
    """Test basic magic_factory behavior."""

    @magic_factory(labels=False)
    def factory(x: int = 1):
        return x

    rep = repr(factory)
    assert rep.startswith("MagicFactory(function=<function test_magic_factory_repr")
    assert rep.endswith("labels=False)")

    @magic_factory(labels=False, x={"widget_type": "Slider"})
    def factory2(x: int = 1):
        return x

    assert repr(factory2).endswith(
        "labels=False, param_options={'x': {'widget_type': 'Slider'}})"
    )


def test_magic_factory_only_takes_kwargs():
    @magic_factory(labels=False)
    def factory(x: int = 1):
        return x

    with pytest.raises(ValueError) as e:
        factory("positional")
        assert "only accept keyword arguments" in str(e)


@magic_factory
def self_referencing_factory(x: int = 1):
    """Function that refers to itself, and wants the FunctionGui instance."""
    return self_referencing_factory


def test_magic_factory_self_reference():
    """Test that self-referential factories work in global scopes."""
    widget = self_referencing_factory()
    assert isinstance(widget(), FunctionGui)


def test_magic_local_factory_self_reference():
    """Test that self-referential factories work in local scopes."""

    @magic_factory
    def local_self_referencing_factory(x: int = 1):
        return local_self_referencing_factory

    widget = local_self_referencing_factory()
    assert isinstance(widget(), FunctionGui)


def test_factory_init():
    def bomb(e):
        raise RuntimeError("boom")

    def widget_init(widget):
        widget.called.connect(bomb)

    @magic_factory(widget_init=widget_init)
    def factory(x: int = 1):
        pass

    widget = factory()

    with pytest.raises(RuntimeError):
        widget()


def test_bad_value_factory_init():
    def widget_init():
        pass

    with pytest.raises(TypeError):

        @magic_factory(widget_init=widget_init)  # type: ignore
        def factory(x: int = 1):
            pass


def test_bad_type_factory_init():

    with pytest.raises(TypeError):

        @magic_factory(widget_init=1)  # type: ignore
        def factory(x: int = 1):
            pass


def test_none_defaults():
    """Make sure that an unannotated parameter with default=None is ok."""

    @magic_factory
    def factory(arg=None):
        return 1

    assert factory()() == 1
