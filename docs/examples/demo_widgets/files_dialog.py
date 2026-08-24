"""# File dialog widget

A dialog to select multiple files.
"""

from collections.abc import Sequence
from pathlib import Path

from magicgui import magicgui


# Sequence of paths
# We change the label using "label" for added clarity
# the filter argument restricts file types
@magicgui(filenames={"label": "Choose Tiff files:", "filter": "*.tif"})
def filespicker(filenames: Sequence[Path]) -> Sequence[Path]:
    """Take a filename and do something with it."""
    print("The filenames are:", filenames)
    return filenames


filespicker.filenames.changed.connect(print)
filespicker.show(run=True)
