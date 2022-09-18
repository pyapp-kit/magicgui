import os
import sys
import time
from unittest.mock import patch

import pytest

from magicgui._util import debounce, user_cache_dir
from magicgui.widgets import FunctionGui


def test_user_cache_dir():
    ucd = user_cache_dir()
    import sys
    from pathlib import Path

    home = Path.home().resolve()
    if sys.platform == "win32":
        assert str(ucd) == str(home / "AppData" / "Local" / "magicgui" / "Cache")
    elif sys.platform == "darwin":
        assert str(ucd) == str(home / "Library" / "Caches" / "magicgui")
    else:
        assert str(ucd) == str(home / ".cache" / "magicgui")


@pytest.mark.skipif(
    bool(os.getenv("CI") and sys.platform == "win32"),
    reason="persistence test failing on CI",
)
def test_persistence(tmp_path):
    """Test that we can persist values across instances."""

    def _my_func(x: int, y="hello"):
        ...

    with patch("magicgui._util.user_cache_dir", lambda: tmp_path):
        fg = FunctionGui(_my_func, persist=True)
        assert str(tmp_path) in str(fg._dump_path)
        assert fg.x.value == 0
        fg.x.value = 10
        time.sleep(0.3)  # wait for debounce
        fg.y.value = "world"
        time.sleep(0.3)  # wait for debounce

        # second instance should match values of first
        fg2 = FunctionGui(_my_func, persist=True)
        assert fg2.x.value == 10
        assert fg2.y.value == "world"
        assert fg2.__signature__ == fg.__signature__
        assert fg2 is not fg


@pytest.mark.skipif(bool(os.getenv("CI")), reason="debounce test too brittle on CI")
def test_debounce():
    store = []

    @debounce(wait=0.1)
    def func(x):
        store.append(x)

    for i in range(10):
        func(i)
        time.sleep(0.034)
    time.sleep(0.15)

    assert len(store) <= 7  # exact timing will vary on CI ... fails too much
    assert store[-1] == 9
