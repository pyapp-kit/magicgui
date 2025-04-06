from __future__ import annotations

from typing import TYPE_CHECKING, Callable, ClassVar, Iterable

from textual.app import App
from textual.binding import Binding
from textual.timer import Timer
from textual.widgets import Footer

from magicgui.widgets.protocols import BaseApplicationBackend

if TYPE_CHECKING:
    from textual.message import Message
    from textual.widget import Widget


class MguiApp(App):
    BINDINGS = [
        ("ctrl+t", "app.toggle_dark", "Toggle Dark mode"),
        ("ctrl+s", "app.screenshot()", "Screenshot"),
        Binding("ctrl+c,ctrl+q", "app.quit", "Quit", show=True),
    ]

    HEADER = None
    FOOTER = Footer()

    _mgui_widgets: ClassVar[list[Widget]] = []

    def compose(self) -> Iterable[Widget]:
        if self.HEADER is not None:
            yield self.HEADER
        yield from self._mgui_widgets
        yield self.FOOTER


class ApplicationBackend(BaseApplicationBackend):
    _app: ClassVar[MguiApp | None] = None

    @classmethod
    def _instance(cls) -> MguiApp:
        """Return the current instance of the application backend."""
        if not hasattr(cls, "__instance"):
            cls.__instance = MguiApp()
        return cls.__instance

    def _mgui_get_backend_name(self) -> str:
        return "textual"

    def _mgui_process_events(self) -> None: ...

    def _mgui_run(self, **kwargs) -> None:
        self._mgui_get_native_app().run(**kwargs)

    def _mgui_quit(self) -> None:
        return self._mgui_get_native_app().exit()

    def _mgui_get_native_app(self) -> App:
        # Get native app
        return self._instance()

    def _mgui_start_timer(
        self,
        interval: int = 0,
        on_timeout: Callable[[], None] | None = None,
        single: bool = False,
    ) -> None:
        # TODO: not sure what to do with these yet...
        event_target = MessageTarget()
        sender = MessageTarget()
        self._timer = Timer(
            event_target=event_target,
            interval=interval / 1000,
            sender=sender,
            callback=on_timeout,
            repeat=1 if single else None,
        )
        self._timer.start()

    def _mgui_stop_timer(self) -> None:
        if getattr(self, "_timer", None):
            self._timer.stop()


class MessageTarget:
    async def post_message(self, message: Message) -> bool: ...

    async def _post_priority_message(self, message: Message) -> bool: ...

    def post_message_no_wait(self, message: Message) -> bool: ...
