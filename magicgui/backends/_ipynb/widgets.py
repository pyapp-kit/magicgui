from ipywidgets import widgets as ipywdg

from magicgui.widgets import _protocols


class Slider(_protocols.RangedWidgetProtocol):

    _ipywidget: ipywdg.Widget

    def __init__(self, qwidg: ipywdg.Widget = ipywdg.IntSlider):
        self._ipywidget = qwidg()

    def _mgui_hide_widget(self):
        pass

    def _mgui_show_widget(self):
        pass

    def _mgui_get_enabled(self):
        ...  # noqa

    def _mgui_set_enabled(self, enabled):
        ...  # noqa

    def _mgui_get_parent(self):
        ...  # noqa

    def _mgui_set_parent(self, widget):
        ...  # noqa

    def _mgui_get_native_widget(self):
        return self._ipywidget  # noqa

    def _mgui_bind_parent_change_callback(self, callback):
        ...  # noqa

    def _mgui_render(self):
        ...  # noqa

    def _mgui_get_width(self):
        ...  # noqa

    def _mgui_set_min_width(self, value: int):
        ...  # noqa

    def _mgui_bind_change_callback(self, callback):
        ...  # noqa

    def _mgui_get_value(self) -> float:
        return self._ipywidget.value

    def _mgui_set_value(self, value: float) -> None:
        self._ipywidget.value = value

    def _mgui_get_min(self) -> float:
        return self._ipywidget.min

    def _mgui_set_min(self, value: float) -> None:
        self._ipywidget.min = value

    def _mgui_get_max(self) -> float:
        return self._ipywidget.max

    def _mgui_set_max(self, value: float) -> None:
        self._ipywidget.max = value

    def _mgui_get_step(self) -> float:
        return self._ipywidget.step

    def _mgui_set_step(self, value: float) -> None:
        self._ipywidget.step = value

    def _mgui_set_orientation(self, value) -> None:
        raise NotImplementedError()

    def _mgui_get_orientation(self) -> str:
        raise NotImplementedError()

    # def orientation(self):
    #     return "horizontal"

    def _ipython_display_(self, **kwargs):
        return self._ipywidget._ipython_display_(**kwargs)


a: _protocols.RangedWidgetProtocol = Slider()
