"""# Image widget.

Example of creating an Image Widget from a file.

(This requires pillow, or that magicgui was installed as ``magicgui[image]``)
"""

from pathlib import Path

from magicgui.widgets import Image

img = Path(__file__).parent.parent.parent / "images" / "_test.jpg"
image = Image(value=str(img))
image.scale_widget_to_image_size()
image.show(run=True)
