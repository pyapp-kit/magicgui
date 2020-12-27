import pytest
from typing_extensions import Annotated

from magicgui.signature import magic_signature, make_annotated, split_annotated_type


def test_make_annotated_raises():
    """Test options to annotated must be a dict."""
    with pytest.raises(TypeError):
        make_annotated(int, "not a dict")  # type: ignore


def test_make_annotated_works_with_already_annotated():
    """Test that make_annotated merges options with Annotated types."""
    annotated_type = Annotated[int, {"max": 10}]  # type: ignore
    assert make_annotated(annotated_type) == annotated_type
    assert (
        make_annotated(annotated_type, {"min": 1})
        == Annotated[int, {"max": 10, "min": 1}]
    )


def test_split_annotated_raises():
    """Test split_annotated raises on bad input."""
    with pytest.raises(TypeError):
        split_annotated_type(int)

    with pytest.raises(TypeError):
        split_annotated_type(Annotated[int, 1])


def _sample_func(a: int, b: str = "hi"):
    pass


def test_magic_signature_raises():
    """Test that gui_options must have keys that are params in function."""
    with pytest.raises(ValueError):
        magic_signature(_sample_func, gui_options={"not_a_param": {"choices": []}})


def test_signature_to_container():
    """Test that a MagicSignature can make a container."""
    sig = magic_signature(_sample_func, gui_options={"a": {"widget_type": "Slider"}})
    container = sig.to_container()
    assert len(container) == 2
    assert repr(container) == "<Container (a: int = 0, b: str = 'hi')>"
    assert repr(container.a) == "Slider(value=0, annotation=<class 'int'>, name='a')"
    assert repr(sig.parameters["a"]) == '<MagicParameter "a: int" {}>'
