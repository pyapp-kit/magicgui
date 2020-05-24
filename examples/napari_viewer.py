"""Example showing how to access the current napari viewer

"""
import skimage.data
import skimage.filters

import napari
from magicgui import magicgui, register_type


def get_viewers(gui, *args):
    """Get the viewer that the magicwidget is in."""
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
        """Just print the viewer."""
        print(viewer)

    # instantiate the widget
    gui = takes_viewer.Gui()
    # Add it to the napari viewer
    viewer.window.add_dock_widget(gui)
