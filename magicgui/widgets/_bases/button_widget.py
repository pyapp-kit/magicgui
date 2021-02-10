from typing import Optional

from magicgui.events import EventEmitter
from magicgui.widgets import _protocols

from .value_widget import ValueWidget


class ButtonWidget(ValueWidget):
    """Widget with a value, Wraps ButtonWidgetProtocol.

    Parameters
    ----------
    text : str, optional
        The text to display on the button. If not provided, will use ``name``.
    """

    _widget: _protocols.ButtonWidgetProtocol
    changed: EventEmitter

    def __init__(self, text: Optional[str] = None, **kwargs):
        if text and kwargs.get("label"):
            from warnings import warn

            warn(
                "'text' and 'label' are synonymous for button widgets. To suppress this"
                " warning, only provide one of the two kwargs."
            )
        text = text or kwargs.get("label")
        super().__init__(**kwargs)
        self.text = text or self.name

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        d = super().options.copy()
        d.update({"text": self.text})
        return d

    @property
    def text(self):
        """Text of the widget."""
        return self._widget._mgui_get_text()

    @text.setter
    def text(self, value):
        self._widget._mgui_set_text(value)
