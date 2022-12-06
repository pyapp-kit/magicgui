from __future__ import annotations

import inspect
import sys
from typing import Sequence, TypeVar, Union, get_origin

from docstring_parser import DocstringParam, parse

C = TypeVar("C", bound=type)


def _param_list_to_str(
    param_list: list[DocstringParam], valtype: type | None = None
) -> str:
    """Format Parameters section for numpy docstring from list of tuples."""
    out = []
    out += ["Parameters", len("Parameters") * "-"]
    for param in param_list:
        parts = []
        if param.arg_name:
            parts.append(param.arg_name)

        type_name = param.type_name or "Any"
        # temporary hacky approach to inject the widget specific type into docstrings
        if param.arg_name == "value" and valtype is not None and (type_name == "Any"):
            if isinstance(valtype, TypeVar):
                if getattr(valtype, "__bound__", None):
                    if get_origin(valtype.__bound__) is Union:
                        type_name = " | ".join(
                            [str(c.__name__) for c in valtype.__bound__.__args__]
                        )
                elif getattr(valtype, "__constraints__", None):
                    type_name = " | ".join(
                        [str(c.__name__) for c in valtype.__constraints__]
                    )
            elif hasattr(valtype, "__name__"):
                type_name = valtype.__name__
        if type_name:
            parts.append(type_name)

        if not parts:
            continue
        out += [" : ".join(parts)]
        if param.description and param.description.strip():
            out += [" " * 4 + line for line in param.description.split("\n")]
    out += [""]
    return "\n".join(out)


def merge_super_sigs(
    cls: C, exclude: Sequence[str] = ("widget_type", "kwargs", "args", "kwds", "extra")
) -> C:
    """Merge the signature and kwarg docs from all superclasses, for clearer docs.

    Parameters
    ----------
    cls : Type
        The class being modified
    exclude : tuple, optional
        A list of parameter names to excluded from the merged docs/signature,
        by default ("widget_type", "kwargs", "args", "kwds")

    Returns
    -------
    cls : Type
        The modified class (can be used as a decorator)
    """
    params = {}
    param_docs: list[DocstringParam] = []
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
        # we only go up to the first class that defines Parameters
        if "Parameters" in docstring:
            break

    # sphinx_autodoc_typehints isn't removing the type annotations from the signature
    # so we do it manually when building documentation.
    if sys.argv[-2:] == ["build", "docs"]:
        params = {
            k: v.replace(annotation=inspect.Parameter.empty) for k, v in params.items()
        }

    cls.__init__.__signature__ = inspect.Signature(  # type: ignore
        sorted(params.values(), key=lambda x: x.kind)
    )
    param_docs = [p for p in param_docs if p.arg_name not in exclude]
    cls.__doc__ = (cls.__doc__ or "").split("Parameters")[0].rstrip() + "\n\n"

    valtype = None
    orig_bases = getattr(cls, "__orig_bases__", [])
    if orig_bases:
        args = getattr(orig_bases[0], "__args__", None)
        if args:
            valtype = args[0]

    cls.__doc__ += _param_list_to_str(param_docs, valtype)
    # this makes docs linking work... but requires that all of these be in __init__
    cls.__module__ = "magicgui.widgets"
    return cls
