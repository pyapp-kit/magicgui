"""# Indeterminate progress bar

Example of an indeterminate progress bar for a long running computation
of unknown time.

"""
import time

from superqt.utils import thread_worker

from magicgui import magicgui
from magicgui.tqdm import tqdm


@magicgui(call_button=True, layout="horizontal")
def long_running(sleep_time=5):
    """Long running computation with an indeterminate progress bar."""
    # Here tqdm is not provided an iterable argument, or the 'total' kwarg
    # so it cannot calculate the expected number of iterations
    # which means it will create an indeterminate progress bar
    with tqdm() as pbar:
        # It is best practice to use a separate thread for long running computations
        # This makes the function non-blocking, you can still interact with the widget
        @thread_worker(connect={"finished": lambda: pbar.progressbar.hide()})
        def sleep(secs):
            time.sleep(secs)

        sleep(sleep_time)


long_running.show(run=True)
