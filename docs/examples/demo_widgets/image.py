"""# Image widget.

Example of creating an Image Widget from a file.

(This requires pillow, or that magicgui was installed as ``magicgui[image]``)
"""

from magicgui.widgets import Image

img = "../../images/_test.jpg"
image = Image(value=img)
image.scale_widget_to_image_size()
image.show(run=True)
