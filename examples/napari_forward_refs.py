"""Example of using a ForwardRef to avoid importing a module that provides a widget.

In this example, one might want to create a widget that takes as an argument a napari
Image layer, and returns an Image.  In order to avoid needing to import napari (and
therefore depending directly on napari), it's possible to annotate those parameters with
a *string* representation of the type (rather than the type itself).  This is called a
"forward reference": https://www.python.org/dev/peps/pep-0484/#forward-references
"""
# Note: if you'd like to avoid circular imports, or just want to avoid having your
# linter yell at you for an undefined type annotation, you can place the import
# inside of an `if typing.TYPE_CHECKING` conditional.  This is not evaluated at runtime,
# only when something like mypy is doing type checking.
from typing import TYPE_CHECKING

from magicgui import magicgui

if TYPE_CHECKING:
    import napari


@magicgui(call_button="execute", background={"max": 200})
def subtract_background(
    data: "napari.types.ImageData", background: int = 50
) -> "napari.types.ImageData":
    """Subtract a contstant from the data."""
    if data:
        return data - background


subtract_background.show(run=True)
# now, this example isn't all that interesting on its own (since there will be no Image
# layer in the dropdown) ... but in another package, where you DO import napari,
# you could add this widget to a napari viewer with
# viewer.window.add_dock_widget(subtract_background)
