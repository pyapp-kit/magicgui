from time import sleep

from magicgui import magicgui
from magicgui.tqdm import trange

# if magicui.tqdm.tqdm or trange are used outside of a @magicgui function, (such as in
# interactive use in IPython), then they fall back to the standard terminal output

# If use inside of a magicgui-decorated function
# a progress bar widget will be added to the magicgui container
@magicgui(call_button=True, layout="horizontal")
def long_running(steps=10, delay=0.1):
    """Long running computation with range iterator."""
    # trange(steps) is a shortcut for `tqdm(range(steps))`
    for i in trange(steps):
        sleep(delay)


long_running.show(run=True)
