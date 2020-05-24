"""Example showing how to accomplish a napari parameter sweep with magicgui.

It demonstrates:
1. overriding the default widget type with a custom class
2. the `auto_call` option, which calls the function whenever a parameter changes

"""
import napari
import skimage.data
import skimage.filters
from magicgui import magicgui, register_type
from typing import Type, Tuple


def get_viewers(gui, *args):
    try:
        return (gui.parent().qt_viewer.viewer,)
    except AttributeError:
        return tuple(v for v in globals().values() if isinstance(v, napari.Viewer))


register_type(napari.Viewer, choices=get_viewers)


with napari.gui_qt():
    # create a viewer and add some images
    viewer = napari.Viewer(title="Viewer A")
    viewer.add_image(skimage.data.astronaut(), name="astronaut")

    @magicgui(call_button="call", viewer={"visible": False})
    def takes_viewer(viewer: napari.Viewer):
        """Apply a gaussian blur to ``layer``."""
        print(viewer)

    # instantiate the widget
    gui = takes_viewer.Gui()
    # Add it to the napari viewer
    viewer.window.add_dock_widget(gui)
