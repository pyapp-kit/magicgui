import random
from time import sleep

from magicgui import magicgui
from magicgui.tqdm import tmgrange, tqdm_mgui

# can be used alone (leave=False will make it hide when done)
for i in tmgrange(5, leave=False):
    sleep(0.5)


# can also be used inside of a magicgui decorator
@magicgui(call_button=True)
def long_running(steps=10, delay=0.1):
    """An example of a long running function with a progress bar."""
    for i in tmgrange(steps):
        sleep(delay)


long_running.show(run=True)


@magicgui(call_button=True, layout="vertical")
def long_function(
    steps=10, repeats=4, choices="ABCDEFGHIJKLMNOP12345679", char="", delay=0.05
):
    # using the `tmgrange` shortcut instead of range()
    for r in tmgrange(repeats, label="repeats", leave=False):
        letters = [random.choice(choices) for _ in range(steps)]
        # `tqdm_gui`, like `tqdm`, accepts any iterable
        # this progress bar is nested and will be run & reset multiple times
        for letter in tqdm_mgui(letters, label="steps", leave=False):
            long_function.char.value = letter
            sleep(delay)


long_function.show(run=True)
