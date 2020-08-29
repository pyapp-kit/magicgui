"""FileDialog with magicgui."""
from pathlib import Path
from typing import Sequence

from magicgui import event_loop, magicgui


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
    filepicker.show()
    filespicker.show()
    filepicker.filename.changed.connect(lambda e: print(e.value.value))
    filespicker.filenames.changed.connect(lambda e: print(e.value.value))
