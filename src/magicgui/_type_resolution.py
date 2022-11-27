import sys
import types
import typing
from copy import copy
from functools import lru_cache, partial
from importlib import import_module
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

# required for python 3.8 to strip annotations
from typing_extensions import get_type_hints

try:
    from toolz import curry

    PARTIAL_TYPES: Tuple[Type, ...] = (partial, curry)
except ImportError:  # pragma: no cover
    PARTIAL_TYPES = (partial,)


@lru_cache(maxsize=1)
def _typing_names() -> Dict[str, Any]:
    return {**typing.__dict__, **types.__dict__}


def _unwrap_partial(func: Any) -> Any:
    while isinstance(func, PARTIAL_TYPES):
        func = func.func
    return func


def resolve_types(
    obj: Union[Callable, types.ModuleType, types.MethodType, type],
    globalns: Optional[Dict[str, Any]] = None,
    localns: Optional[Dict[str, Any]] = None,
    do_imports: bool = False,
) -> Dict[str, Any]:
    """Resolve type hints from an object.

    Parameters
    ----------
    obj : Union[Callable, types.ModuleType, types.MethodType, type]
        Object to resolve type hints from.
    globalns : Optional[Dict[str, Any]]
        Global namespace to resolve imports from.
    localns : Optional[Dict[str, Any]]
        Local namespace to resolve imports from.
    do_imports : bool
        If `True`, will attempt to import modules when a NameError is
        encountered while resolving hints. For example, resolving `numpy.ndarray`
        will `import numpy` if a NameError is encountered.  By default, `False`.
    """
    # inject typing names into localns for convenience
    _localns = dict(_typing_names())
    # explicitly provided locals take precedence
    localns = {**_localns, **localns} if localns else _localns
    obj = _unwrap_partial(obj)

    try:
        hints = get_type_hints(obj, globalns=globalns, localns=localns)  # type: ignore
    except NameError as e:
        if do_imports:
            # try to import the top level name and try again
            msg = str(e)
            if msg.startswith("name ") and msg.endswith(" is not defined"):
                name = msg.split()[1].strip("\"'")
                ns = dict(localns) if localns else {}
                if name not in ns:
                    ns[name] = import_module(name)
                    return resolve_types(obj, globalns, ns, do_imports=do_imports)
        raise e

    # before version 3.9, typing.get_type_hints did not resolve hint.__args__
    if sys.version_info < (3, 9):
        _iterdict(hints, _resolve_forwards)
    return hints


def _iterdict(d: Dict[str, Any], func: Callable) -> None:
    for k, v in d.items():
        if isinstance(v, dict):
            _iterdict(v, func)
        else:
            d[k] = func(v)


def _resolve_forwards(v: Any) -> Any:
    if isinstance(v, typing.ForwardRef):
        return _try_cached_resolve(v.__forward_arg__)
    if getattr(v, "__args__", ()):
        v = copy(v)
        v.__args__ = tuple(_resolve_forwards(a) for a in v.__args__)
    return v


def resolve_single_type(
    hint: Any,
    globalns: Optional[Dict[str, Any]] = None,
    localns: Optional[Dict[str, Any]] = None,
    do_imports: bool = True,
) -> Any:
    """Resolve a single type hint.

    See `resolve_types` for details on parameters.
    """
    if hint is None:
        return None
    mock_obj = type("_T", (), {"__annotations__": {"obj": hint}})()
    hints = resolve_types(mock_obj, globalns, localns, do_imports=do_imports)
    return hints["obj"]


_cached_resolve = lru_cache(maxsize=None)(resolve_single_type)


def _try_cached_resolve(v: Any) -> Any:
    try:
        return _cached_resolve(v)
    except TypeError:
        return resolve_single_type(v)
