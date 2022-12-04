from pathlib import Path

import mkdocs_gen_files

from magicgui import widgets
from magicgui.backends import _ipynb, _qtpy

IMAGES = False
BACKENDS = {"qt": _qtpy.widgets, "ipynb": _ipynb.widgets}
WIDGETS_PATH = Path("widgets")
BASES_PATH = Path("bases")
WIDGET_PAGE = """
# {name}

{img_link}

Available in backends: {backends}

::: magicgui.widgets.{name}
    handler: widget_handler
"""


def _snap_image(_obj: type, _name: str) -> str:
    try:
        wdg = _obj().native
    except Exception:
        return ""
    else:
        pth = WIDGETS_PATH / "images" / f"{_name}.png"
        with mkdocs_gen_files.open(pth, "wb") as f:
            wdg.setMinimumWidth(300)  # turns out this is very important for grab
            wdg.grab().save(f.name)
        return (
            f'![{_name} widget](../{pth}){{{{ loading=lazy, class="widget-image" }}}}'
        )


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

        img_link = _snap_image(obj, name) if IMAGES else ""
        with mkdocs_gen_files.open(WIDGETS_PATH / f"{name}.md", "w") as f:
            md = WIDGET_PAGE.format(
                name=name, backends=", ".join(backends), img_link=img_link
            )
            f.write(md)


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
