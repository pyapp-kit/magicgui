"""FileDialog with magicgui."""
from pathlib import Path
from magicgui import event_loop, magicgui


@magicgui(filename={"mode": "existing_file", "filter": "Images (*.tif *.tiff)"})
def filepicker(filename=Path("~")):
    """Take a filename and do something with it."""
    print("The filename is:", filename)
    return filename


with event_loop():
    gui = filepicker.Gui(show=True)
    gui.filename_changed.connect(print)
