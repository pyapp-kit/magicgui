"""problematic functions"""

from magicgui import magicgui, event_loop
from skimage import filters
from skimage.data import grass
from functools import partial


with event_loop():
    for n in [
        # "frangi",
        # "hessian",
        # "inverse",
        # "meijering",
        "sato",
        # "try_all_threshold",
        # "wiener",
    ]:
        func = partial(getattr(filters, n), grass())
        gui = magicgui(func, call_button="print").Gui(show=True)
        gui.called.connect(print)
