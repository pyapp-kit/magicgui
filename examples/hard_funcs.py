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
        func = magicgui(func, call_button="print")
        func.called.connect(print)
        func.show()
