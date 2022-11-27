import importlib.abc
import sys
import types
from contextlib import contextmanager
from importlib import import_module
from importlib.machinery import ModuleSpec
from textwrap import dedent
from typing import Any

from griffe.dataclasses import Alias
from griffe.docstrings import numpy
from mkdocstrings_handlers.python.handler import PythonHandler

# TODO: figure out how to do this with options
@contextmanager
def _hide_numpy_warn():
    before, numpy._warn = numpy._warn, lambda *x, **k: None
    yield
    numpy._warn = before


def inject_dynamic_docstring(item: Alias, identifier: str) -> None:
    module, name = identifier.rsplit(".", 1)
    obj = getattr(import_module(module), name)
    first_line, *rest = (obj.__doc__ or "").splitlines()
    if first_line and item.target.docstring:
        item.target.docstring.value = first_line + "\n" + dedent("\n".join(rest))


class WidgetHandler(PythonHandler):
    def collect(self, identifier: str, config: dict) -> Any:
        item = super().collect(identifier, config)
        if isinstance(item, Alias):
            inject_dynamic_docstring(item, identifier)
        # to edit default in the parameter table
        # item.parameters["something"].default = ...
        return item

    def render(self, data: Any, config: dict) -> str:
        with _hide_numpy_warn():
            return super().render(data, config)


class MyLoader(importlib.abc.Loader):
    def create_module(self, spec):
        return types.ModuleType(spec.name)

    def exec_module(self, module: types.ModuleType):
        def get_handler(**kwargs):
            return WidgetHandler(handler="python", **kwargs)

        module.get_handler = get_handler


class Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, *args, **kwargs) -> ModuleSpec | None:
        if fullname == "mkdocstrings_handlers.widget_handler":
            return ModuleSpec(fullname, MyLoader())
        return None


def on_startup(**kwargs):
    sys.meta_path.append(Finder())
