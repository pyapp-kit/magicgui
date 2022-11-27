from typing import Any, Optional

from psygnal import Signal, SignalInstance

from magicgui.widgets import protocols

from ._value_widget import ValueWidget


class ButtonWidget(ValueWidget[bool]):
    """Widget with a value, Wraps ButtonWidgetProtocol.

    Parameters
    ----------
    text : str, optional
        The text to display on the button. If not provided, will use ``name``.
    """

    _widget: protocols.ButtonWidgetProtocol
    changed = Signal(object)

    def __init__(self, text: Optional[str] = None, **value_widget_kwargs: Any) -> None:
        if text and value_widget_kwargs.get("label"):
            from warnings import warn

            warn(
                "'text' and 'label' are synonymous for button widgets. To suppress this"
                " warning, only provide one of the two kwargs."
            )
        text = text or value_widget_kwargs.get("label")
        # TODO: make a backend hook that lets backends inject their optional API
        # ipywidgets button texts are called descriptions
        text = text or value_widget_kwargs.pop("description", None)
        super().__init__(**value_widget_kwargs)
        self.text = (text or self.name).replace("_", " ")

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        d = super().options.copy()
        d.update({"text": self.text})
        return d

    @property
    def text(self) -> str:
        """Text of the widget."""
        return self._widget._mgui_get_text()

    @text.setter
    def text(self, value: str) -> None:
        self._widget._mgui_set_text(value)

    @property
    def clicked(self) -> SignalInstance:
        """Alias for changed event."""
        return self.changed
