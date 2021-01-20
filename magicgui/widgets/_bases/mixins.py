from magicgui.widgets import _protocols


class _OrientationMixin:
    """Properties for classes wrapping widgets that support orientation."""

    _widget: _protocols.SupportsOrientation

    @property
    def orientation(self) -> str:
        """Orientation of the widget."""
        return self._widget._mgui_get_orientation()

    @orientation.setter
    def orientation(self, value: str) -> None:
        if value not in {"horizontal", "vertical"}:
            raise ValueError(
                "Only horizontal and vertical orientation are currently supported"
            )
        self._widget._mgui_set_orientation(value)
