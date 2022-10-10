from magicgui.widgets._protocols import BaseApplicationBackend


class ApplicationBackend(BaseApplicationBackend):
    def _mgui_get_backend_name(self):
        return "ipynb"

    def _mgui_process_events(self):
        raise NotImplementedError()

    def _mgui_run(self):
        pass  # We run in IPython, so we don't run!

    def _mgui_quit(self):
        pass  # We don't run so we don't quit!

    def _mgui_get_native_app(self):
        return self

    def _mgui_start_timer(self, interval=0, on_timeout=None, single=False):
        raise NotImplementedError()

    def _mgui_stop_timer(self):
        raise NotImplementedError()
