"""# Directory dialog widget

A dialog to select a directory.
"""

from pathlib import Path

from magicgui import magicgui


# Select a directory, instead of file(s)
@magicgui(directory={"mode": "d", "label": "Choose a directory"})
def directorypicker(directory=Path("~")):
    """Take a directory name and do something with it."""
    print("The directory name is:", directory)
    return directory


directorypicker.directory.changed.connect(print)
directorypicker.show(run=True)
