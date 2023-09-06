"""# napari Qt demo

Napari provides a few conveniences with magicgui, and one of the
most commonly used is the layer combo box that gets created when
a parameter is annotated as napari.layers.Layer.

The layer box will stay in sync with the viewer model, adding and
removing layers as needed.

This example shows how to use just that widget in the context
of a larger custom QWidget.
"""
import napari
from qtpy.QtWidgets import QVBoxLayout, QWidget

from magicgui.widgets import create_widget


class CustomWidget(QWidget):
    """A custom widget class."""

    def __init__(self) -> None:
        super().__init__()
        self.setLayout(QVBoxLayout())
        # change annotation to napari.layers.Image (e.g) to restrict to just Images
        self._layer_combo = create_widget(annotation=napari.layers.Layer)
        # magicgui widgets hold the Qt widget at `widget.native`
        self.layout().addWidget(self._layer_combo.native)


viewer = napari.Viewer()
viewer.add_points()
viewer.add_points()

my_widget = CustomWidget()
viewer.window.add_dock_widget(my_widget)

# when my_widget is a magicgui.Widget, it will detect that it has been added
# to a viewer, and automatically update the choices.  Otherwise, you need to
# trigger this yourself:
my_widget._layer_combo.reset_choices()
viewer.layers.events.inserted.connect(my_widget._layer_combo.reset_choices)
viewer.layers.events.removed.connect(my_widget._layer_combo.reset_choices)

napari.run()
