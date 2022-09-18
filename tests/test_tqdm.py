"""Tests for the tqdm wrapper."""
from time import sleep

import pytest

from magicgui import magicgui

tqdm = pytest.importorskip("tqdm", reason="need tqdm installed to test tqdm")
from magicgui.tqdm import tqdm, trange  # noqa


def test_tqdm_outside_of_functiongui():
    """Test that we can make a tqdm wrapper with ProgressBar outside of @magicgui."""
    with trange(10) as pbar:
        assert pbar.n == 0
        assert pbar.total == 10
        assert not pbar._mgui

    assert tuple(trange(5)) == tuple(range(5))


def test_disabled_tqdm():
    """Test that a disabled tqdm does not have a progressbar or magicgui."""

    @magicgui
    def f():
        with trange(10, disable=True) as pbar:
            assert not hasattr(pbar, "progressbar")
            assert not pbar._mgui


def test_no_leave_tqdm():
    """Test that leave=False hides the progressbar when done (tqdm API wording)"""

    @magicgui
    def f():
        with trange(10, leave=True) as pbar1:
            pass
        assert pbar1.progressbar.visible is True

    f.show()
    f()

    @magicgui
    def f2():
        with trange(10, leave=False) as pbar2:
            pass
        assert pbar2.progressbar.visible is False

    f2.show()
    f2()


def test_unbound_tqdm():
    """Test that tqdm without defined total sill have a range of (0, 0)."""

    @magicgui
    def f():
        with tqdm() as pbar:
            assert pbar.total is None
            # undefined range will render as a "busy" indicator
            assert pbar.progressbar.range == (0, 0)

    f.show()
    f()


def test_tqdm_std_err(capsys):
    """Test that tqdm inside an invisible magicgui falls back to console behavior."""

    # outside of a magicgui it falls back to tqdm_std behavior
    with tqdm(range(10)) as t_obj:
        iter(t_obj)
    captured = capsys.readouterr()

    assert "0%|" in str(captured.err)
    assert "| 0/10" in str(captured.err)
    assert not str(captured.out)


def test_tqdm_in_visible_mgui_std_err(capsys):
    """Test that tqdm inside an mgui outputs to console only when mgui not visible."""

    # inside of a of a magicgui it falls back to tqdm_std behavior
    @magicgui
    def f():
        with tqdm(range(10)) as t_obj:
            iter(t_obj)

    f()
    captured = capsys.readouterr()
    assert "0%|" in str(captured.err)
    assert "| 0/10" in str(captured.err)
    assert not str(captured.out)

    # showing the widget disables the output to console behavior
    f.show()
    f()
    captured = capsys.readouterr()
    assert not str(captured.err)
    assert not str(captured.out)


# Test various ways that tqdm might need to traverse the frame stack:


def test_tqdm_inside_of_magicgui():
    """Test that tqdm can find the magicgui within which it is called."""

    @magicgui
    def long_func(steps=2):
        for i in tqdm([0, 1]):
            sleep(0.02)

    # before calling the function, we won't have any progress bars
    long_func.show()
    assert not long_func._tqdm_pbars
    long_func()
    # after calling the it, we should now have a progress bars
    assert len(long_func._tqdm_pbars) == 1
    # but calling it again won't add more
    long_func()
    assert len(long_func._tqdm_pbars) == 1


def test_trange_inside_of_magicgui():
    """Test that trange can find the magicgui within which it is called."""

    @magicgui
    def long_func(steps=2):
        for i in trange(4):
            pass

    long_func.show()
    assert not long_func._tqdm_pbars
    long_func()
    assert len(long_func._tqdm_pbars) == 1


def _indirectly_decorated(steps=2):
    for i in trange(4):
        pass


def test_trange_inside_of_indirectly_decorated_magicgui():
    """Test that trange can find the magicgui within which it is called."""
    indirectly_decorated = magicgui(_indirectly_decorated)
    indirectly_decorated.show()
    assert not indirectly_decorated._tqdm_pbars
    indirectly_decorated()
    assert len(indirectly_decorated._tqdm_pbars) == 1


def test_tqdm_nested():
    """Test that tqdm can find the magicgui within which it is called."""

    @magicgui
    def long_func():
        for i in trange(4):
            for x in trange(4):
                pass

    long_func.show()
    # before calling the function, we won't have any progress bars
    assert not long_func._tqdm_pbars
    long_func()
    # after calling the it, we should now have a progress bars
    assert len(long_func._tqdm_pbars) == 2

    # the depth is all that matters... not the total number of tqdms
    @magicgui
    def long_func2():
        for i in trange(4):
            for x in trange(4):
                pass

        for x in trange(4):
            pass

    long_func2.show()
    # before calling the function, we won't have any progress bars
    assert not long_func2._tqdm_pbars
    long_func2()
    # after calling the it, we should now have a progress bars
    assert len(long_func2._tqdm_pbars) == 2
