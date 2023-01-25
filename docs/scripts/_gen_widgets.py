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


# values just for the sake of making the images for docs
VALS = {
    widgets.Password: "password",
    widgets.FileEdit: "/Users/user/Desktop",
    widgets.FloatRangeSlider: (200, 800),
    widgets.RangeSlider: (200, 800),
    widgets.CheckBox: True,
    widgets.LineEdit: "Some value",
    widgets.TextEdit: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
    widgets.Label: "Some label",
    widgets.LiteralEvalLineEdit: "{'a': 1, 'b': 2}",
    widgets.ProgressBar: 420,
    widgets.QuantityEdit: "1 meter",
    widgets.Slider: 42,
    widgets.Table: [{"a": 1, "b": 2}, {"a": 3, "b": 4}],
}


def _add_value(obj: widgets.bases.ValueWidget) -> None:

    if isinstance(obj, widgets.bases.ButtonWidget):
        obj.text = "Click me!"

    if obj.__class__ in VALS:
        obj.value = VALS[obj.__class__]
        return

    if isinstance(obj, widgets.bases.CategoricalWidget):
        obj.choices = ["Choice A", "Choice B", "Choice C"]
        obj.value = "Choice A"

    if isinstance(obj, widgets.Dialog):
        obj.append(widgets.Label(value="Are you sure?"))


def _snap_image(_obj: type, _name: str) -> str:
    from qtpy.QtWidgets import QVBoxLayout, QWidget

    outer = QWidget()
    if obj is widgets.Container:
        return ""
    if issubclass(obj, widgets.FunctionGui):
        return ""
    if issubclass(obj, (widgets.TupleEdit, widgets.ListEdit)):
        wdg = _obj(value=(1, 2, 3))
    else:
        wdg = _obj()
    _add_value(wdg)
    outer.setLayout(QVBoxLayout())
    outer.layout().addWidget(wdg.native)
    pth = IMAGES_PATH / f"{_name}.png"
    with mkdocs_gen_files.open(pth, "wb") as f:
        outer.setMinimumWidth(300)  # turns out this is very important for grab
        outer.grab().save(f.name)
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
