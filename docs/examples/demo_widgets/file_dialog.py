"""# File dialog widget

A dialog to select a file.
"""

from pathlib import Path

from magicgui import magicgui


@magicgui(filename={"mode": "r"})
def filepicker(filename=Path("~")) -> Path:
    """Take a filename and do something with it."""
    print("The filename is:", filename)
    return filename


filepicker.filename.changed.connect(print)
filepicker.show(run=True)
