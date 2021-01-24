from magicgui import magicgui
from magicgui.widgets import ProgressBar


@magicgui(call_button="tick", pbar={"min": 0, "step": 2, "max": 20, "value": 0})
def manual(pbar: ProgressBar, increment: bool = True):
    """Example of manual progress bar control."""
    if increment:
        pbar.increment()
    else:
        pbar.decrement()


manual.show(run=True)
