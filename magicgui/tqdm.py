import inspect
from typing import Optional

from magicgui.application import use_app
from magicgui.function_gui import FunctionGui
from magicgui.widgets import ProgressBar

try:
    from tqdm import tqdm
except ImportError as e:
    msg = (
        f"{e}. To use magicgui with tqdm please `pip install tqdm`, "
        "or use the tqdm extra: `pip install magicgui[tqdm]`"
    )
    raise type(e)(msg)


def _find_parent_container() -> Optional[FunctionGui]:
    """Traverse calling stack looking for a magicgui container."""
    for frame_info in inspect.stack()[1:]:
        calling_func = frame_info.frame.f_globals.get(frame_info.function)
        if isinstance(calling_func, FunctionGui):
            return calling_func
    return None


_tqdm_kwargs = {
    p.name
    for p in inspect.signature(tqdm.__init__).parameters.values()
    if p.kind is not inspect.Parameter.VAR_KEYWORD and p.name != "self"
}


class tqdm_mgui(tqdm):
    """magicgui version of tqdm."""

    disable: bool

    def __init__(self, *args, **kwargs) -> None:
        kwargs = kwargs.copy()

        pbar_kwargs = {k: kwargs.pop(k) for k in set(kwargs) - _tqdm_kwargs}
        kwargs["gui"] = True
        kwargs.setdefault("mininterval", 0.025)
        # check if we're being instantiated inside of a magicgui container
        self._mgui = _find_parent_container()
        super().__init__(*args, **kwargs)

        self.sp = lambda x: None  # no-op status printer, required for older tqdm compat
        if self.disable:
            return

        self._app = use_app()
        assert self._app.native

        self.progressbar = (
            self._mgui._push_tqdm_pbar(pbar_kwargs)
            if self._mgui
            else ProgressBar(**pbar_kwargs)
        )
        if self.total is not None:
            # initialize progress bar range
            self.progressbar.range = (self.n, self.total)
            self.progressbar.value = self.n
        else:
            # show a busy indicator instead of a percentage of steps
            self.progressbar.range = (0, 0)
        self.progressbar.show()

    def close(self) -> None:
        """Cleanup and (if leave=False) close the progressbar."""
        if self.disable:
            return

        # Prevent multiple closures
        self.disable = True

        with self._lock:
            try:
                self._instances.remove(self)
            except KeyError:
                pass

        with self._lock:
            if not self.leave:
                self._app.process_events()
                self.progressbar.hide()
            if self._mgui:
                self._mgui._pop_tqdm_pbar()

    def display(self, msg: str = None, pos: int = None) -> None:
        """Update the display."""
        self.progressbar.value = self.n
        self._app.process_events()


def tmgrange(*args, **kwargs) -> tqdm_mgui:
    """Shortcut for tqdm_mgui(range(*args), **kwargs)."""
    return tqdm_mgui(range(*args), **kwargs)
