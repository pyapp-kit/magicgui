"""problematic functions"""

from functools import partial

from skimage import filters
from skimage.data import grass

from magicgui import event_loop, magicgui

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
