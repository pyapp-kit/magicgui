"""A wrapper around the tqdm.tqdm iterator that adds a ProgressBar to a magicgui."""
import inspect
from typing import Iterable, Optional, cast

from magicgui.application import use_app
from magicgui.widgets import FunctionGui, ProgressBar

try:
    from tqdm import tqdm as _tqdm_std
except ImportError as e:  # pragma: no cover
    msg = (
        f"{e}. To use magicgui with tqdm please `pip install tqdm`, "
        "or use the tqdm extra: `pip install magicgui[tqdm]`"
    )
    raise type(e)(msg)


def _find_calling_function_gui(max_depth=6) -> Optional[FunctionGui]:
    """Traverse calling stack looking for a magicgui FunctionGui."""
    for finfo in inspect.stack()[2:max_depth]:

        # regardless of whether the function was decorated directly in the global module
        # namespace, or if it was renamed on decoration (`new_name = magicgui(func)`),
        # or if it was decorated inside of some local function scope...
        # we will eventually hit the :meth:`FunctionGui.__call__` method, which will
        # have the ``FunctionGui`` instance as ``self`` in its locals namespace.
        if finfo.function == "__call__" and finfo.filename.endswith("function_gui.py"):
            obj = finfo.frame.f_locals.get("self")
            if isinstance(obj, FunctionGui):
                return obj
            return None  # pragma: no cover

    return None


_tqdm_kwargs = {
    p.name
    for p in inspect.signature(_tqdm_std.__init__).parameters.values()
    if p.kind is not inspect.Parameter.VAR_KEYWORD and p.name != "self"
}


class tqdm(_tqdm_std):
    """magicgui version of tqdm.

    See tqdm.tqdm API for valid args and kwargs: https://tqdm.github.io/docs/tqdm/

    Also, any keyword arguments to the :class:`magicgui.widgets.ProgressBar` widget
    are also accepted and will be passed to the ``ProgressBar``.

    Examples
    --------
    When used inside of a magicgui-decorated function, ``tqdm`` (and the
    ``trange`` shortcut function) will append a visible progress bar to the gui
    container.

    >>> @magicgui(call_button=True)
    ... def long_running(steps=10, delay=0.1):
    ...     for i in tqdm(range(steps)):
    ...         sleep(delay)

    nesting is also possible:

    >>> @magicgui(call_button=True)
    ... def long_running(steps=10, repeats=4, delay=0.1):
    ...     for r in trange(repeats):
    ...         for s in trange(steps):
    ...             sleep(delay)
    """

    disable: bool

    def __init__(self, iterable: Iterable = None, *args, **kwargs) -> None:
        kwargs = kwargs.copy()
        pbar_kwargs = {k: kwargs.pop(k) for k in set(kwargs) - _tqdm_kwargs}
        self._mgui = _find_calling_function_gui()
        if self._in_visible_gui:
            kwargs["gui"] = True
            kwargs.setdefault("mininterval", 0.025)
        super().__init__(iterable, *args, **kwargs)
        if not self._in_visible_gui:
            return

        self.sp = lambda x: None  # no-op status printer, required for older tqdm compat
        if self.disable:
            return

        # check if we're being instantiated inside of a magicgui container
        self.progressbar = self._get_progressbar(**pbar_kwargs)
        self._app = use_app()

        if self.total is not None:
            # initialize progress bar range
            self.progressbar.range = (self.n, self.total)
            self.progressbar.value = self.n
        else:
            # show a busy indicator instead of a percentage of steps
            self.progressbar.range = (0, 0)
        self.progressbar.show()

    @property
    def _in_visible_gui(self) -> bool:
        try:
            return self._mgui is not None and self._mgui.visible
        except RuntimeError:
            return False

    def _get_progressbar(self, **kwargs) -> ProgressBar:
        """Create ProgressBar or get from the parent gui `_tqdm_pbars` deque.

        The deque allows us to create nested iterables inside of a magigui, while
        resetting and reusing progress bars across ``FunctionGui`` calls. The nesting
        depth (into the deque) is reset by :meth:`FunctionGui.__call__`, right before
        the function is called.  Then, as the function encounters `tqdm` instances,
        this method gets or creates a progress bar and increment the
        :attr:`FunctionGui._tqdm_depth` counter on the ``FunctionGui``.
        """
        if self._mgui is None:
            return ProgressBar(**kwargs)

        if len(self._mgui._tqdm_pbars) > self._mgui._tqdm_depth:
            pbar = self._mgui._tqdm_pbars[self._mgui._tqdm_depth]
        else:
            pbar = ProgressBar(**kwargs)
            self._mgui._tqdm_pbars.append(pbar)
            self._mgui.append(pbar)
        self._mgui._tqdm_depth += 1
        return pbar

    def display(self, msg: str = None, pos: int = None) -> None:
        """Update the display."""
        if not self._in_visible_gui:
            return super().display(msg=msg, pos=pos)

        self.progressbar.value = self.n
        self._app.process_events()

    def close(self) -> None:
        """Cleanup and (if leave=False) close the progressbar."""
        if not self._in_visible_gui:
            return super().close()
        self._mgui = cast(FunctionGui, self._mgui)

        if self.disable:
            return

        # Prevent multiple closures
        self.disable = True

        # remove from tqdm instance set
        with self._lock:
            try:
                self._instances.remove(self)
            except KeyError:  # pragma: no cover
                pass

            if not self.leave:
                self._app.process_events()
                self.progressbar.hide()

        self._mgui._tqdm_depth -= 1


def trange(*args, **kwargs) -> tqdm:
    """Shortcut for tqdm(range(*args), **kwargs)."""
    return tqdm(range(*args), **kwargs)
