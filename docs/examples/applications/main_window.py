import pathlib
from enum import Enum

from magicgui import magicgui


class HotdogOptions(Enum):
    """All hotdog possibilities"""

    Hotdog = 1
    NotHotdog = 0


@magicgui(main_window=True, layout="form", call_button="Classify", result_widget=True)
def is_hotdog(img: pathlib.Path) -> HotdogOptions:
    """Classify possible hotdog images.

    Upload an image and check whether it's an hotdog. For example, this image
    will be classified as one: <br><br>

    <img src="resources/hotdog.jpg">

    Parameters
    ----------
    img : pathlib.Path
        Path to a possible hotdog image

    Returns
    -------
    HotdogOptions
        True if image contains an hotdog in it
    """
    if "hotdog" in img.stem:
        return HotdogOptions.Hotdog
    return HotdogOptions.NotHotdog


if __name__ == "__main__":
    is_hotdog.show(run=True)
