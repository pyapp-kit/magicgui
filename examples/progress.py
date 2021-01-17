import random
from time import sleep

from magicgui import magicgui
from magicgui.tqdm import tmgrange, tqdm_mgui
from magicgui.widgets import ProgressBar

# can be used alone (outside of a magicgui)
# `tmgrange(*args, **kwargs)` is a shortcut for tqdm_mgui(range(*args), **kwargs)
# (..., leave=False) will make the progressbar hide when done
for i in tmgrange(10, leave=False):
    sleep(0.1)


# can also be used inside of a magicgui decorator
# in which case the progress bar will be added to the magicgui container
@magicgui(call_button=True)
def long_running(steps=10, delay=0.1):
    """Long running computation with range iterator."""
    for i in tmgrange(steps):
        sleep(delay)


long_running.show(run=True)


# nested progress bars is possible


@magicgui(call_button=True, layout="vertical")
def long_function(
    steps=10, repeats=4, choices="ABCDEFGHIJKLMNOP12345679", char="", delay=0.05
):
    """Long running computation with nested iterators."""
    # tmgrange and tqdm_gui accept all the kwargs from tqdm itself, as well as any
    # valid kwargs for magicgui.widgets.ProgressBar, (such as "label")
    for r in tmgrange(repeats, label="repeats"):
        letters = [random.choice(choices) for _ in range(steps)]
        # `tqdm_gui`, like `tqdm`, accepts any iterable
        # this progress bar is nested and will be run & reset multiple times
        for letter in tqdm_mgui(letters, label="steps"):
            long_function.char.value = letter
            sleep(delay)


long_function.show(run=True)

# or you can annotate a parameter as ProgressBar and have full control with `value`
# `min`, `max`, `step`, `increment(val=self.step)`, `decrement(val=self.step)`, etc...


@magicgui(call_button="tick", pbar={"min": 0, "step": 2, "max": 20, "value": 0})
def manual(pbar: ProgressBar, increment: bool = True):
    """Example of manual progress bar control."""
    if increment:
        pbar.increment()
    else:
        pbar.decrement()


manual.show(run=True)
