from tqdm import tqdm

from magicgui.application import use_app
from magicgui.widgets import ProgressBar


class tqdm_mgui(tqdm):
    """magicgui version of tqdm."""

    disable: bool

    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs["gui"] = True
        kwargs.setdefault("mininterval", 0.025)
        super().__init__(*args, **kwargs)
        self.sp = None  # required for older compat
        if self.disable:
            return

        self._app = use_app()
        assert self._app.native
        self.progressbar = ProgressBar(name="tqdm_mgui")
        self.progressbar.show()
        if self.total is not None:
            print("toata", self.total)
            self.progressbar.range = (self.n, self.total)
            self.progressbar.value = self.n
        else:
            self.progressbar.range = (0, 0)

    def close(self):
        """Cleanup and (if leave=False) close the progressbar."""
        if self.disable:
            return

        self.disable = True

        with self.get_lock():
            self._instances.remove(self)

        if self.leave:
            self.display()
        else:
            self.progressbar.hide()
            self._app.process_events()

    def clear(self, nolock=False):
        """Clear current bar display."""
        # need to override to prevent calling self.sp()
        pass

    def display(self, msg=None, pos=None):
        """Update the display."""
        self.progressbar.value = self.n
        self._app.process_events()
