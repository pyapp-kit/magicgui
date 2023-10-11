from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from psygnal import Signal, SignalInstance

from magicgui.types import Undefined, _Undefined

from ._value_widget import ValueWidget

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from magicgui.widgets import protocols

    from ._widget import WidgetKwargs


class ButtonWidget(ValueWidget[bool]):
    """Widget with a value, Wraps a widget implementing the ButtonWidgetProtocol.

    >see [ButtonWidgetProtocol][magicgui.widgets.protocols.ButtonWidgetProtocol].

    Parameters
    ----------
    value : bool
        The starting state of the widget.
    text : str, optional
        The text to display on the button. If not provided, will use ``name``.
    bind : Callable[[ValueWidget], Any] | Any, optional
        A value or callback to bind this widget. If provided, whenever
        [`widget.value`][magicgui.widgets.bases.ValueWidget.value] is
        accessed, the value provided here will be returned instead. `bind` may be a
        callable, in which case `bind(self)` will be returned (i.e. your bound callback
        must accept a single parameter, which is this widget instance).
    nullable : bool, optional
        If `True`, the widget will accepts `None` as a valid value, by default `False`.
    **base_widget_kwargs : Any
        All additional keyword arguments are passed to the base
        [`magicgui.widgets.Widget`][magicgui.widgets.Widget] constructor.
    """

    _widget: protocols.ButtonWidgetProtocol
    changed = Signal(
        object,
        description="Emitted when the button is clicked (may also be "
        "connected at the alias `clicked`).",
    )

    def __init__(
        self,
        value: bool | _Undefined = Undefined,
        *,
        text: str | None = None,
        icon: str | None = None,
        icon_color: str | None = None,
        bind: bool | Callable[[ValueWidget], bool] | _Undefined = Undefined,
        nullable: bool = False,
        **base_widget_kwargs: Unpack[WidgetKwargs],
    ) -> None:
        if text and base_widget_kwargs.get("label"):
            from warnings import warn

            warn(
                "'text' and 'label' are synonymous for button widgets. To suppress this"
                " warning, only provide one of the two kwargs.",
                stacklevel=2,
            )
        text = text or base_widget_kwargs.get("label")
        # TODO: make a backend hook that lets backends inject their optional API
        # ipywidgets button texts are called descriptions
        text = text or base_widget_kwargs.pop("description", None)
        super().__init__(
            value=value, bind=bind, nullable=nullable, **base_widget_kwargs
        )
        self.text = (text or self.name).replace("_", " ")
        if icon:
            self.set_icon(icon, icon_color)

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

    def set_icon(self, value: str | None, color: str | None = None) -> None:
        self._widget._mgui_set_icon(value, color)
