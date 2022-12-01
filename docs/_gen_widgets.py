from pathlib import Path

import mkdocs_gen_files

from magicgui import widgets
from magicgui.backends import _ipynb, _qtpy

BACKENDS = {"qt": _qtpy.widgets, "ipynb": _ipynb.widgets}
WIDGETS_PATH = Path("widgets")
BASES_PATH = Path("bases")
WIDGET_PAGE = """
# {name}

Available in backends: {backends}

::: magicgui.widgets.{name}
    handler: widget_handler
"""

for name in dir(widgets):
    if name.startswith("_"):
        continue
    obj = getattr(widgets, name)
    if (
        isinstance(obj, type)
        and issubclass(obj, widgets.Widget)
        and obj is not widgets.Widget
        and obj.__name__ == name
    ):
        backends = [
            f"`{key}`" for key, module in BACKENDS.items() if hasattr(module, name)
        ]

        with mkdocs_gen_files.open(WIDGETS_PATH / f"{name}.md", "w") as f:
            f.write(WIDGET_PAGE.format(name=name, backends=", ".join(backends)))

BASE_PAGE = """
# {name}

::: magicgui.widgets.bases.{name}
"""

for base in [
    "Widget",
    "ButtonWidget",
    "CategoricalWidget",
    "ContainerWidget",
    "DialogWidget",
    "MainWindowWidget",
    "RangedWidget",
    "SliderWidget",
    "ValueWidget",
]:
    with mkdocs_gen_files.open(BASES_PATH / f"{base}.md", "w") as f:
        f.write(BASE_PAGE.format(name=base))
