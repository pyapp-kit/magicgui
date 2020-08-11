from __future__ import annotations

import signal
from contextlib import contextmanager
from importlib import import_module
from types import ModuleType
from typing import Iterator, Optional, Union

from magicgui.backends import BACKENDS
from magicgui.bases import BaseApplicationBackend


@contextmanager
def event_loop(backend=None) -> Iterator:
    """Start an event loop in which to run the application."""
    with Application(backend) as app:
        yield app


class Application:
    """MagicGui Application, wrapping a native BaseApplicationBackend implementation."""

    _backend_module: ModuleType
    _backend: BaseApplicationBackend
    _instance: Optional[Application] = None

    def __init__(self, backend_name: Optional[str] = None):
        self._use(backend_name)

    @property
    def backend_name(self) -> str:
        """Return name of the GUI backend that this app wraps."""
        if self._backend is not None:
            return self._backend._mg_get_backend_name()
        else:
            return ""

    @property
    def backend_module(self) -> ModuleType:
        """Return module object that defines the backend."""
        return self._backend_module

    def _use(self, backend_name=None):
        """Select a backend by name."""
        if not backend_name:
            backend_name = "qt"
        if not backend_name or backend_name.lower() not in BACKENDS:
            raise ValueError(
                f"backend_name must be one of {set(BACKENDS)!r}, "
                f"not {backend_name!r}"
            )

        module_name, native_module_name = BACKENDS[backend_name]
        self._backend_module = import_module(f"magicgui.backends.{module_name}")
        self._backend = self.get_obj("ApplicationBackend")()

    def get_obj(self, name: str):
        try:
            return getattr(self.backend_module, name)
        except AttributeError as e:
            raise AttributeError(
                f"Could not retrieve object {name} from backend {self.backend_module}"
            ) from e

    def run(self):
        """Enter the native GUI event loop."""
        return self._backend._mg_run()

    @property
    def native(self):
        """Return the native GUI application instance."""
        return self._backend._mg_get_native_app()

    def quit(self):
        """Quit the native GUI event loop."""
        return self._backend._mg_quit()

    def create(self):
        """Create the native application."""
        # Ensure that the native app exists
        self.native

    def process_events(self):
        """Process all pending GUI events."""
        return self._backend._mg_process_events()

    def __repr__(self):
        """Return repr for this instance."""
        if not self.backend_name:
            return "<magicgui app with no backend>"
        else:
            return f"<magicgui app, wrapping the {self.backend_name} GUI toolkit>"

    def __enter__(self):
        """Context manager to start this application."""
        self.create()
        return self

    def __exit__(self, *exc_details):
        """Exit context manager for this application."""
        # enable ctrl-C
        signal.signal(signal.SIGINT, lambda *a: self.quit())
        self._backend._mg_start_timer(500, lambda: None)
        self._backend._mg_run()
        self._backend._mg_stop_timer()


# TODO: make this not default to qt
def _use_app(backend_name: str = "qt"):
    """Get/create the default Application object.

    It is safe to call this function multiple times, as long as
    backend_name is None or matches the already selected backend.

    Parameters
    ----------
    backend_name : str | None
        The name of the backend application to use. If not specified, Vispy
        tries to select a backend automatically. See ``vispy.use()`` for
        details.
    """
    # If we already have a default_app, raise error or return
    current = Application._instance
    if current is not None:
        names = current.backend_name.lower().replace("(", " ").strip(") ")
        _nm = [n for n in names.split(" ") if n]
        if backend_name and backend_name.lower() not in _nm:
            raise RuntimeError("Can only select a backend once, already using {_nm}.")
        else:
            return current  # Current backend matches backend_name

    # Create default app
    Application._instance = Application(backend_name)
    return Application._instance


AppRef = Union[Application, str, None]


def use_app(app: AppRef) -> Application:
    """Get/create the default Application object.  See _use_app docstring."""
    if app is None:
        return _use_app()
    elif isinstance(app, Application):
        return app
    elif isinstance(app, str):
        return Application(app)
    raise TypeError(f"'app' must be string, Application, or None, got: {app!r}.  ")
