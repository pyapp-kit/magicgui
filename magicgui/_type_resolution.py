import types
import typing
from functools import lru_cache, partial
from importlib import import_module
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union, get_type_hints

try:
    from toolz import curry

    PARTIAL_TYPES: Tuple[Type, ...] = (partial, curry)
except ImportError:  # pragma: no cover
    PARTIAL_TYPES = (partial,)


@lru_cache(maxsize=1)
def _typing_names() -> Dict[str, Any]:
    return {**typing.__dict__, **types.__dict__}  # noqa: TYP006


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
        return get_type_hints(obj, globalns=globalns, localns=localns)
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


def resolve_single_type(
    obj: Any,
    globalns: Optional[Dict[str, Any]] = None,
    localns: Optional[Dict[str, Any]] = None,
    do_imports: bool = True,
):
    """Resolve a single type hint from an object."""
    if obj is None:
        return None
    mock_obj = type("_T", (), {"__annotations__": {"obj": obj}})()
    hints = resolve_types(mock_obj, globalns, localns, do_imports=do_imports)
    return hints["obj"]
