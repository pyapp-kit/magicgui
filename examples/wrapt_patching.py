"""Utilities for changing function signatures."""
import inspect
from ast import literal_eval
from collections import OrderedDict, defaultdict
from importlib import import_module
from itertools import chain
from types import ModuleType
import typing  # noqa: F401 - needed for eval() statements
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
    List,
    ForwardRef,  # type: ignore
    _GenericAlias,  # type: ignore
)
import re
import wrapt
from numpydoc.docscrape import FunctionDoc

from magicgui import magicgui

_TYPE_LOOKUP = {
    "int": int,
    "None": type(None),
    "none": type(None),
    "float": float,
    "bool": bool,
    "dict": Dict,
    "boolean": bool,
    "str": str,
    "tuple": Tuple,
    "list": List,
    "scalar": Union[int, float],
    "sequence": Sequence,
    "iterable": Iterable,
    "generator": Generator,
    "function": Callable,
    "callable": Callable,
    "array-like": ForwardRef("numpy.ndarray"),
    "array": ForwardRef("numpy.ndarray"),
}


def typestr_to_typeobj(typestr: str) -> Optional[type]:
    """Convert numpydoc style type string into typing object.

    Parameters
    ----------
    typestr : str
        String describing a paramater type

    Returns
    -------
    type or None
        Type annotation.  If unable to parse, returns None.

    Examples
    --------
    >>> typestr_to_typeobj('int or 3-Tuple of ints, optional')
    typing.Union[int, typing.Tuple[int, int, int], NoneType]
    """
    typestr = typestr.strip().strip(",")

    if typestr.lower() in _TYPE_LOOKUP:
        return _TYPE_LOOKUP[typestr.lower()]

    match = re.match(r"^([\w-]+) of (\w+)$", typestr)
    if match:
        container, inner = match.groups()
        n = None
        if container.lower() not in _TYPE_LOOKUP:
            tupmatch = re.match(r"(\d+)-tuple", container.lower())
            if tupmatch:
                n = int(tupmatch.groups()[0])
                cont_type = Tuple
            else:
                return ForwardRef(container)
        else:
            container = _TYPE_LOOKUP[container.lower()]
        inner_type = _TYPE_LOOKUP.get(inner.lower())
        if not inner_type:
            if inner.lower().endswith("s"):
                inner_type = _TYPE_LOOKUP.get(inner.lower()[:-1])
            else:
                inner_type = ForwardRef(inner)
        if isinstance(n, int) and isinstance(inner_type, (type, _GenericAlias)):
            i = inner_type.__name__ if isinstance(inner_type, type) else str(inner_type)
            return eval(f'Tuple[{", ".join([i] * n)}]')
        return (
            cont_type[inner_type, ...] if cont_type is Tuple else cont_type[inner_type]
        )

    if "optional" in typestr.lower():
        if ", optional" in typestr.lower():
            return Optional[typestr_to_typeobj(typestr.lower().split(", optional")[0])]
        return Optional[typestr_to_typeobj(typestr.replace("optional", ""))]

    if "or" in typestr.lower():
        if "none" in typestr.lower():
            newstr = typestr.lower().replace("none", "").strip()
            return Optional[typestr_to_typeobj(newstr)]
        _types = [typestr_to_typeobj(i) for i in typestr.split("or") if i.strip()]
        # FIXME: is there a better way to do this??
        if all([isinstance(t, (type, _GenericAlias)) for t in _types]):
            ls = [t.__name__ if isinstance(t, type) else str(t) for t in _types]
            return eval(f'Union[{", ".join(ls)}]')

    if any(x in typestr for x in ("array",)):
        return ForwardRef("numpy.ndarray")
    return None


def guess_numpydoc_annotations(func: Callable) -> Dict[str, Dict[str, Any]]:
    """Return a dict with type hints and/or choices for each parameter in the docstring.

    Parameters
    ----------
    func : function
        The function to parse

    Returns
    -------
    param_dict : dict
        dict where the keys are names of parameters in the signature of ``func``, and
        the value is a dict with possible keys ``type``, and ``choices``.  ``type``
        provides a typing object from ``typing`` that can be used in function signatures
    """
    param_dict: Dict[str, Dict[str, Any]] = OrderedDict()
    sig = inspect.signature(func)
    for name, type_, description in FunctionDoc(func).get("Parameters"):
        if name not in sig.parameters:
            continue
        if name not in param_dict:
            param_dict[name] = {}
        if type_.startswith("{'"):
            try:
                param_dict[name]["choices"] = literal_eval(type_.split("},")[0] + "}")
            except Exception:
                pass
        param_dict[name]["type"] = typestr_to_typeobj(type_)
    return param_dict


def change_signature(
    force_annotation: Optional[Dict[str, Type]] = None,
    change_annotation: Optional[Dict[str, Type]] = None,
    namespace: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable], Callable]:
    """Change function signature.

    Parameters
    ----------
    force_annotation : dict, optional
        mapping of {argument_name: type_hint}.  Will force any arguments named
        ``argument_name`` to be annotated as ``type_hint``.
    change_annotation : dict
        mapping of {current_hint: new_hint}.  Will force any arguments currently
        annotated with a type of ``curent_hint`` to ``new_hint`.
    namespace : dict
        mapping of {name: object}.  Namespaces required for importing any types
        declared as type annotations in the other arguments.

    Returns
    -------
    adapter : callable
        The returned function may be provided to the `adapter` argument of the
        ``wrapt.decorator`` function.
    """
    force_annotation = force_annotation or dict()
    change_annotation = change_annotation or dict()
    namespace = namespace or dict()
    if not namespace:
        for val in chain(change_annotation.values(), force_annotation.values()):
            mod = val.__module__.split(".")[0]
            namespace[mod] = import_module(mod)

    def argspec_factory(wrapped):
        sig = inspect.signature(wrapped)
        new_params = OrderedDict(sig.parameters.items())
        for name, param in new_params.items():
            if name in force_annotation:
                new_params[name] = param.replace(annotation=force_annotation[name])
        new_sig = sig.replace(parameters=list(new_params.values()))
        _globals = {}
        exec(f"def _func{new_sig}: pass", namespace, _globals)
        return _globals["_func"]

    return wrapt.adapter_factory(argspec_factory)


def find_functions_with_arg_named(
    module: ModuleType,
    argname: Union[str, Sequence[str]],
    match_all: Optional[bool] = False,
    include_private: Optional[bool] = False,
) -> Generator[Callable, None, None]:
    """Yield all functions in module ``module`` that have an argument named ``argname``.

    Parameters
    ----------
    module : ModuleType
        The module to search
    argname : str or list of str
        name (or names)
    match_all : bool, optional
        if True, all provided argnames must be present in signature to match. by default
        False
    include_private : bool, optional
        if True, include private functions (starting with '_'), by default False.

    Returns
    -------
    Generator[Callable, None, None]
        [description]

    Yields
    ------
    Generator[Callable, None, None]
        [description]
    """
    if isinstance(argname, str):
        argname = [argname]

    for funcname in dir(module):
        if funcname.startswith("_") and not include_private:
            continue
        func = getattr(module, funcname)
        if not inspect.isfunction(func):
            continue
        sig = inspect.signature(func)
        _match = all if match_all else any
        if _match([arg in sig.parameters for arg in argname]):
            yield func


def get_parameter_position(func: Callable, param: str) -> int:
    """Return the position of `param` in the signature of function `func`.

    Parameters
    ----------
    func : Callable
        A function with a signature
    param : str
        The name of the parameter to search for

    Returns
    -------
    int
        The position of the parameter in the signature, or -1 if not found.
    """
    try:
        return next(
            i
            for i, p in enumerate(inspect.signature(func).parameters.values())
            if p.name == param
        )
    except StopIteration:
        return -1


if __name__ == "__main__":
    from skimage import filters
    from qtpy.QtWidgets import QApplication

    import napari

    change_image_to_layer = change_signature({"image": napari.layers.Layer})

    @wrapt.decorator(adapter=change_image_to_layer)
    def image_as_napari_layer(wrapped, instance=None, args=None, kwargs=None):
        """Return decorator that converts skimage functions to accept napari layers."""
        image_idx = get_parameter_position(wrapped, "image")
        if len(args) >= (image_idx + 1):
            args = list(args)
            if hasattr(args[image_idx], "data"):
                args[image_idx] = args[image_idx].data
        elif "image" in kwargs:
            if hasattr(kwargs["image"], "data"):
                kwargs["image"] = kwargs["image"].data
        return wrapped(*args, **kwargs)

    adapted_functions = [
        image_as_napari_layer(f)
        for f in find_functions_with_arg_named(filters, "image")
    ]

    guis = {}
    for func in adapted_functions:
        opts: Dict[str, Any] = defaultdict(dict)
        opts.update({"ignore": ["output"], "auto_call": True})
        annotations = guess_numpydoc_annotations(func)
        for pname, value in annotations.items():
            if "choices" in value:
                opts[pname]["choices"] = value["choices"]
            # if "type" in value:
            #     opts[pname]["dtype"] = value["type"]
        guis[func.__name__] = magicgui(func, **opts)

    app = QApplication([])
    for func in guis.values():
        func.Gui()
