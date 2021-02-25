import time
from unittest.mock import patch

from magicgui._util import user_cache_dir
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


def test_persistence(tmp_path):
    """Test that we can persist values across instances."""

    def _my_func(x: int, y="hello"):
        ...

    with patch("magicgui._util.user_cache_dir", lambda: tmp_path):
        fg = FunctionGui(_my_func, persist=True)
        assert str(tmp_path) in str(fg._dump_path)
        assert fg.x.value == 0
        fg.x.value = 10
        time.sleep(0.26)  # required by rate limit
        fg.y.value = "world"

        # second instance should match values of first
        fg2 = FunctionGui(_my_func, persist=True)
        assert fg2.x.value == 10
        assert fg2.y.value == "world"
        assert fg2.__signature__ == fg.__signature__
        assert fg2 is not fg
