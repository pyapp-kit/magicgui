from __future__ import annotations

import inspect
import os
import sys
import time
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, overload

from docstring_parser import DocstringParam, parse

if TYPE_CHECKING:
    from typing import TypeVar

    from typing_extensions import ParamSpec

    T = TypeVar("T")
    P = ParamSpec("P")
    C = TypeVar("C", bound=type)


@overload
def debounce(function: Callable[P, T]) -> Callable[P, T | None]: ...


@overload
def debounce(
    *, wait: float = 0.2
) -> Callable[[Callable[P, T]], Callable[P, T | None]]: ...


def debounce(function: Callable[P, T] | None = None, wait: float = 0.2) -> Callable:
    """Postpone function call until `wait` seconds since last invocation."""

    def decorator(fn: Callable[P, T]) -> Callable[P, T | None]:
        from threading import Timer

        _store: dict = {"timer": None, "last_call": 0.0, "args": (), "kwargs": {}}

        @wraps(fn)
        def debounced(*args: P.args, **kwargs: P.kwargs) -> T | None:
            _store["args"] = args
            _store["kwargs"] = kwargs

            def call_it() -> T:
                _store["timer"] = None
                _store["last_call"] = time.time()
                return fn(*_store["args"], **_store["kwargs"])

            if not _store["last_call"]:
                return call_it()

            if _store["timer"] is None:
                time_since_last_call = time.time() - _store["last_call"]
                _store["timer"] = Timer(wait - time_since_last_call, call_it)
                _store["timer"].start()  # type: ignore
            return None

        return debounced

    return decorator if function is None else decorator(function)  # type: ignore


def throttle(t: float) -> Callable[[Callable[P, T]], Callable[P, T | None]]:
    """Prevent a function from being called more than once in `t` seconds."""

    def decorator(f: Callable[P, T]) -> Callable[P, T | None]:
        last = [0.0]

        @wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            if last[0] and (time.time() - last[0] < t):
                return None
            last[0] = time.time()
            return f(*args, **kwargs)

        return wrapper

    return decorator


# modified from appdirs: https://github.com/ActiveState/appdirs
# License: MIT
def user_cache_dir(
    appname: str | None = "magicgui", version: str | None = None
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
    """  # noqa: E501
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


def safe_issubclass(obj: object, superclass: object) -> bool:
    """Safely check if obj is a subclass of superclass."""
    try:
        return issubclass(obj, superclass)  # type: ignore
    except Exception:
        return False


def _param_list_to_str(
    param_list: list[DocstringParam], other_params: list[DocstringParam]
) -> str:
    """Format Parameters section for numpy docstring from list of tuples."""
    out = []
    out += ["Parameters", len("Parameters") * "-"]
    for param in param_list:
        parts = []
        if param.arg_name:
            parts.append(param.arg_name)
        if param.type_name:
            parts.append(param.type_name)
        if not parts:
            continue
        out += [" : ".join(parts)]
        if param.description and param.description.strip():
            out += [" " * 4 + line for line in param.description.split("\n")]
    out += [""]
    return "\n".join(out)


def merge_super_sigs(
    cls: C,
    exclude: Iterable[str] = (
        "widget_type",
        "kwargs",
        "args",
        "kwds",
        "extra",
        "backend_kwargs",
    ),
    module: str = "magicgui.widgets",
) -> C:
    """Merge the signature and kwarg docs from all superclasses, for clearer docs.

    This can be used as a decorator, but must be used with a function call, (even
    if you don't pass any arguments).

    Parameters
    ----------
    cls : Type
        The class being modified
    exclude : tuple, optional
        A list of parameter names to excluded from the merged docs/signature,
        by default ("widget_type", "kwargs", "args", "kwds")
    module : str
        A module name to assign to `cls.__module__`.

    Returns
    -------
    cls : Type
        The modified class (can be used as a decorator)
    """
    params = {}
    param_docs: list[DocstringParam] = []
    other_params: list[DocstringParam] = []
    for sup in inspect.getmro(cls):
        try:
            sig = inspect.signature(sup.__init__)  # type: ignore
        # in some environments `object` or `abc.ABC` will raise ValueError here
        except ValueError:
            continue
        for name, param in sig.parameters.items():
            if name in exclude:
                continue
            params[name] = param

        docstring = getattr(sup, "__doc__", "")
        param_docs += parse(docstring).params
        if "Parameters" in docstring:
            break

    # sphinx_autodoc_typehints isn't removing the type annotations from the signature
    # so we do it manually when building documentation.
    if sys.argv[-2:] == ["build", "docs"]:  # if building docs
        params = {
            k: v.replace(annotation=inspect.Parameter.empty) for k, v in params.items()
        }

    cls.__init__.__signature__ = inspect.Signature(  # type: ignore
        sorted(params.values(), key=lambda x: x.kind)
    )
    param_docs = [p for p in param_docs if p.arg_name not in exclude]
    cls.__doc__ = (cls.__doc__ or "").split("Parameters")[0].rstrip() + "\n\n"
    cls.__doc__ += _param_list_to_str(param_docs, other_params)
    # this makes docs linking work... but requires that all of these be in __init__
    cls.__module__ = module
    return cls


# def mergedoc(
#     cls: type,
#     exclude: Iterable[str] = (
#         "widget_type",
#         "kwargs",
#         "args",
#         "kwds",
#         "extra",
#         "backend_kwargs",
#     ),
# ):
#     from textwrap import indent

#     from griffe.dataclasses import Docstring
#     from griffe.docstrings.dataclasses import DocstringParameter, DocstringSection
#     from griffe.docstrings.numpy import parse

#     super_docs: dict[str, list[DocstringSection]] = {}
#     for sup in cls.__mro__:
#         docstring = getattr(sup, "__doc__", None)
#         if docstring:
#             super_docs[sup.__name__] = parse(Docstring(docstring))

#     seen = set(exclude)
#     for base, sections in super_docs.items():
#         print(">>", base)
#         for section in sections:
#             if section.kind.name == "parameters":
#                 for p in section.value:
#                     if p.name in seen:
#                         # continue
#                         ...
#                     p = cast(DocstringParameter, p)
#                     desc = indent(p.description, ' ' * 4)
#                     line = f"{p.name} : {p.annotation}\n{desc}"
#                     seen.add(p.name)
#                     print(line)
