import os
import sys
import time
from functools import wraps
from pathlib import Path
from typing import Optional


def debounce(function=None, wait: float = 0.2):
    """Postpone function call until `wait` seconds since last invokation."""

    def decorator(fn):
        from threading import Timer

        _store: dict = {"timer": None, "last_call": 0.0, "args": (), "kwargs": {}}

        @wraps(fn)
        def debounced(*args, **kwargs):
            _store["args"] = args
            _store["kwargs"] = kwargs

            def call_it():
                _store["timer"] = None
                _store["last_call"] = time.time()
                return fn(*_store["args"], **_store["kwargs"])

            if not _store["last_call"]:
                return call_it()

            if _store["timer"] is None:
                time_since_last_call = time.time() - _store["last_call"]
                _store["timer"] = Timer(wait - time_since_last_call, call_it)
                _store["timer"].start()  # type: ignore

        return debounced

    if function is None:
        return decorator
    else:
        return decorator(function)


def throttle(t):
    """Prevent a function from being called more than once in `t` seconds."""

    def decorator(f):
        last = [0.0]

        @wraps(f)
        def wrapper(*args, **kwargs):
            if last[0] and (time.time() - last[0] < t):
                return
            last[0] = time.time()
            return f(*args, **kwargs)

        return wrapper

    return decorator


# modified from appdirs: https://github.com/ActiveState/appdirs
# License: MIT
def user_cache_dir(
    appname: Optional[str] = "magicgui", version: Optional[str] = None
) -> Path:
    r"""Return full path to the user-specific cache dir for this application.

    Typical user cache directories are:
        Mac OS X:   ~/Library/Caches/<AppName>
        Unix:       ~/.cache/<AppName> (XDG default)
        Win XP:     C:\Documents and Settings\<username>\Local Settings\Application Data\<AppName>\Cache  # noqa
        Vista:      C:\Users\<username>\AppData\Local\<AppName>\Cache

    Parameters
    ----------
    appname : str, optional
        Name of application. If None, just the system directory is returned.
        by default "magicgui"
    version : str, optional
        an optional version path element to append to the path. You might want to use
        this if you want multiple versions of your app to be able to run independently.
        If used, this would typically be "<major>.<minor>". Only applied when appname is
        present.

    Returns
    -------
    str
        Full path to the user-specific cache dir for this application.
    """
    if sys.platform.startswith("java"):
        import platform

        os_name = platform.java_ver()[3][0]
        if os_name.startswith("Windows"):  # "Windows XP", "Windows 7", etc.
            system = "win32"
        elif os_name.startswith("Mac"):  # "Mac OS X", etc.
            system = "darwin"
        else:  # "Linux", "SunOS", "FreeBSD", etc.
            # Setting this to "linux2" is not ideal, but only Windows or Mac
            # are actually checked for and the rest of the module expects
            # *sys.platform* style strings.
            system = "linux2"
    else:
        system = sys.platform

    home = Path.home()
    if system == "win32":
        _epath = os.getenv("LOCALAPPDATA")
        path = Path(_epath).resolve() if _epath else home / "AppData" / "Local"
        if appname:
            path = path / appname / "Cache"
    elif system == "darwin":
        path = home / "Library" / "Caches"
        if appname:
            path = path / appname
    else:
        _epath = os.getenv("XDG_CACHE_HOME")
        path = Path(_epath) if _epath else home / ".cache"
        if appname:
            path = path / appname
    if appname and version:
        path = path / version
    return path
