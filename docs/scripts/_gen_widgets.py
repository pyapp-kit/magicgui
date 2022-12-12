import subprocess
from pathlib import Path

import mkdocs_gen_files

from magicgui import widgets
from magicgui.backends import _ipynb, _qtpy

MAKE_IMAGES = True
BACKENDS = {"qt": _qtpy.widgets, "ipynb": _ipynb.widgets}
WIDGETS_PATH = Path("api/widgets")
IMAGES_PATH = Path("images")
WIDGET_PAGE = """
# {name}

{img_link}

Available in backends: {backends}

::: magicgui.widgets.{name}
    handler: widget_handler
"""


def _set_dark_mode(dark_mode: bool):
    """Set the system to dark mode or not."""
    cmd = ["osascript", "-l", "JavaScript", "-e"]
    if dark_mode:
        cmd += ["Application('System Events').appearancePreferences.darkMode = true"]
    else:
        cmd += ["Application('System Events').appearancePreferences.darkMode = false"]
    subprocess.run(cmd)


def _snap_image(_obj: type, _name: str) -> str:
    try:
        wdg = _obj().native
    except Exception:
        return ""
    else:
        pth = IMAGES_PATH / f"{_name}.png"
        with mkdocs_gen_files.open(pth, "wb") as f:
            wdg.setMinimumWidth(300)  # turns out this is very important for grab
            wdg.grab().save(f.name)
        return f'![{_name} widget](../../{pth}){{ loading=lazy, class="widget-image" }}'


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

        img_link = _snap_image(obj, name) if MAKE_IMAGES else ""
        with mkdocs_gen_files.open(WIDGETS_PATH / f"{name}.md", "w") as f:
            md = WIDGET_PAGE.format(
                name=name, backends=", ".join(backends), img_link=img_link
            )
            f.write(md)
