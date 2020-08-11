from magicgui.bases import BaseApplicationBackend


# qt implementation
class ApplicationBackend(BaseApplicationBackend):
    def _mg_get_backend_name(self):
        return "ThisBackendsName"

    def _mg_process_events(self):
        raise NotImplementedError()

    def _mg_run(self):
        raise NotImplementedError()

    def _mg_quit(self):
        raise NotImplementedError()

    def _mg_get_native_app(self):
        raise NotImplementedError()

    def _mg_start_timer(self, interval=0, on_timeout=None, single=False):
        raise NotImplementedError()

    def _mg_stop_timer(self):
        raise NotImplementedError()
