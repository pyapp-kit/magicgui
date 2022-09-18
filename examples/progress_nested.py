import random
from time import sleep

from magicgui import magicgui
from magicgui.tqdm import tqdm, trange

# if magicui.tqdm.tqdm or trange are used outside of a @magicgui function, (such as in
# interactive use in IPython), then they fall back to the standard terminal output


# If use inside of a magicgui-decorated function
# a progress bar widget will be added to the magicgui container
@magicgui(call_button=True, layout="vertical")
def long_function(
    steps=10, repeats=4, choices="ABCDEFGHIJKLMNOP12345679", char="", delay=0.05
):
    """Long running computation with nested iterators."""
    # trange and tqdm accept all the kwargs from tqdm itself, as well as any
    # valid kwargs for magicgui.widgets.ProgressBar, (such as "label")
    for r in trange(repeats, label="repeats"):
        letters = [random.choice(choices) for _ in range(steps)]
        # `tqdm`, like `tqdm`, accepts any iterable
        # this progress bar is nested and will be run & reset multiple times
        for letter in tqdm(letters, label="steps"):
            long_function.char.value = letter
            sleep(delay)


long_function.show(run=True)
