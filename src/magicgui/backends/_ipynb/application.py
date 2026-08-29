from __future__ import annotations

import asyncio
from collections.abc import Callable

from magicgui.widgets.protocols import BaseApplicationBackend


class ApplicationBackend(BaseApplicationBackend):
    _timer_handle: asyncio.TimerHandle | None = None

    def _mgui_get_backend_name(self):
        return "ipynb"

    def _mgui_process_events(self):
        # ipywidgets updates are pushed to the frontend over the kernel's comm
        # channels as traits change, so there is nothing to flush synchronously
        pass

    def _mgui_run(self):
        pass  # We run in IPython, so we don't run!

    def _mgui_quit(self):
        pass  # We don't run so we don't quit!

    def _mgui_get_native_app(self):
        return self

    def _mgui_start_timer(
        self,
        interval: int = 0,
        on_timeout: Callable[[], None] | None = None,
        single: bool = False,
    ):
        self._mgui_stop_timer()
        # in a Jupyter kernel, cells are executed inside a running asyncio loop
        loop = asyncio.get_running_loop()
        interval_s = interval / 1000

        def _tick() -> None:
            self._timer_handle = None if single else loop.call_later(interval_s, _tick)
            if on_timeout is not None:
                on_timeout()

        self._timer_handle = loop.call_later(interval_s, _tick)

    def _mgui_stop_timer(self):
        if self._timer_handle is not None:
            self._timer_handle.cancel()
            self._timer_handle = None
