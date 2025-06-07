"""# Image widget

Example of creating an Image Widget from a file.

(This requires pillow, or that magicgui was installed as ``magicgui[image]``)
"""

from pathlib import Path

from magicgui.widgets import Image

try:
    test_jpg = Path(__file__).parent.parent.parent / "images" / "_test.jpg"
except NameError: # hack to support mkdocs-gallery build, which doesn't define __file__
    test_jpg = "../../images/_test.jpg"

image = Image(value=test_jpg)
image.scale_widget_to_image_size()
image.show(run=True)
