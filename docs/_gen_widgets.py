import mkdocs_gen_files
from pathlib import Path
from magicgui import widgets
from magicgui.widgets import bases

BASES = [bases.ValueWidget, bases.ContainerWidget]
WIDGETS = Path("widgets")

for name in dir(widgets):
    if name.startswith("_"):
        continue
    obj = getattr(widgets, name)
    if not isinstance(obj, type):
        continue
    if not issubclass(obj, widgets.Widget):
        continue
    if obj.__name__ != name:
        continue
    with mkdocs_gen_files.open(WIDGETS / f"{name}.md", "w") as f:
        f.write(f"# {name}\n\n")
        f.write(f"::: magicgui.widgets.{name}\n    handler: widget_handler\n\n")