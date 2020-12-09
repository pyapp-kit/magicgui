from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QApplication

from magicgui.widgets._protocols import BaseApplicationBackend


# qt implementation
class ApplicationBackend(BaseApplicationBackend):
    _app: QApplication

    def _mgui_get_backend_name(self):
        return "qt"

    def _mgui_process_events(self):
        app = self._mgui_get_native_app()
        app.flush()
        app.processEvents()

    def _mgui_run(self):
        app = self._mgui_get_native_app()
        # only start the event loop if magicgui created it
        if app.objectName() == "magicgui":
            return app.exec_()

    def _mgui_quit(self):
        return self._mgui_get_native_app().quit()

    def _mgui_get_native_app(self):
        # Get native app
        self._app = QApplication.instance()
        if not self._app:
            self._app = QApplication([])
            self._app.setObjectName("magicgui")
        return self._app

    def _mgui_start_timer(self, interval=0, on_timeout=None, single=False):
        self._timer = QTimer()
        if on_timeout:
            self._timer.timeout.connect(on_timeout)
        self._timer.setSingleShot(single)
        self._timer.setInterval(interval)
        self._timer.start()

    def _mgui_stop_timer(self):
        if getattr(self, "_timer", None):
            self._timer.stop()
