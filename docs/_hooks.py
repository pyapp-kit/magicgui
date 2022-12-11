"""https://www.mkdocs.org/dev-guide/plugins/#events ."""
import importlib.abc
import sys
import types
from contextlib import contextmanager
from importlib import import_module
from importlib.machinery import ModuleSpec
from itertools import count
from pathlib import Path
from textwrap import dedent
from typing import Any

from griffe.dataclasses import Alias
from griffe.docstrings import numpy
from mkdocstrings_handlers.python.handler import PythonHandler

from magicgui.type_map import get_widget_class


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


def _replace_autosummary(md: str) -> str:
    lines = md.splitlines()
    start = lines.index("::: autosummary")
    last_line = lines.index("", start + 1)
    table = ["| Widget | Description |", "| ---- | ----------- |"]
    for line in lines[start + 1 : last_line]:
        name = line.strip()
        if name:
            module, _name = name.rsplit(".", 1)
            obj = getattr(import_module(module), _name)
            table.append(f"| [`{_name}`][{name}] | {obj.__doc__.splitlines()[0]} |")

    lines[start:last_line] = table
    return "\n".join(lines)


def _replace_type_to_widget(md: str) -> str:
    lines = md.splitlines()
    start = lines.index("::: type_to_widget")
    try:
        last_line = lines.index("", start + 1)
    except ValueError:
        last_line = None
    table = [
        "| <div style='width:210px'>Type</div> "
        "| <div style='width:100px'>Default Widget</div> "
        "| Additional kwargs",
        "| ---- | ------ | ------ |",
    ]
    for line in lines[start + 1 : last_line]:
        name = line.strip()
        if name:
            wdg_type, kwargs = get_widget_class(annotation=name)
            kwargs.pop("nullable", None)
            kwargs = f"`{kwargs}`" if kwargs else ""
            wdg_name = f"magicgui.widgets.{wdg_type.__name__}"
            wdg_link = f"[`{wdg_type.__name__}`][{wdg_name}]"
            if "[" in name:
                _name = name.split("[")[0]
                name_link = f"[`{name}`][typing.{_name}]"
            else:
                name_link = f"[`{name}`][]"
            table.append(f"| {name_link}  | {wdg_link} | {kwargs} | ")

    lines[start:last_line] = table
    return "\n".join(lines)


def on_page_markdown(md, page, **kwargs):
    import re

    w_iter = count()
    ns: dict = {}

    while "::: autosummary" in md:
        md = _replace_autosummary(md)

    while "::: type_to_widget" in md:
        md = _replace_type_to_widget(md)

    def _sub(matchobj: re.Match) -> str:
        src = matchobj.group(1)
        _md = "```python\n" + src + "\n```"
        if ".show()" in src:
            dest = f"_images/{page.file.name}_{next(w_iter)}.png"
            if _write_markdown_result_image(src, ns, dest):
                _md += f"\n![](../{dest})\n\n"

        return _md

    md = re.sub(r"```python\n([^`]*)```", _sub, md, re.DOTALL)

    return md


def _write_markdown_result_image(src: str, ns: dict, dest: str) -> bool:
    import mkdocs_gen_files
    from qtpy.QtWidgets import QApplication

    Path(dest).parent.mkdir(exist_ok=True, parents=True)
    wdg = set(QApplication.topLevelWidgets())
    exec(src, ns, ns)
    new_wdg = set(QApplication.topLevelWidgets()) - wdg
    if new_wdg:
        for w in new_wdg:
            w.setMinimumWidth(200)
            w.show()

            with mkdocs_gen_files.open(dest, "wb") as f:
                success = w.grab().save(f.name)
            w.close()
            w.deleteLater()
    return success
