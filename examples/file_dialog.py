"""FileDialog with magicgui."""
from pathlib import Path
from magicgui import event_loop, magicgui
from typing import Sequence


# may also add Qt-style filter to filename options:
# e.g. {"filter": "Images (*.tif *.tiff)"}
@magicgui(filename={"mode": "r"})
def filepicker(filename=Path("~")):
    """Take a filename and do something with it."""
    print("The filename is:", filename)
    return filename


# Sequence of paths
@magicgui()
def filespicker(filenames: Sequence[Path]):
    """Take a filename and do something with it."""
    print("The filenames are:", filenames)
    return filenames


with event_loop():
    gui = filepicker.Gui(show=True)
    gui.filename_changed.connect(print)
    gui2 = filespicker.Gui(show=True)
