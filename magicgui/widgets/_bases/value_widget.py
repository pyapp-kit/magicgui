from __future__ import annotations

from typing import Any

from magicgui.events import EventEmitter
from magicgui.widgets import _protocols

from .widget import Widget

UNBOUND = object()


class ValueWidget(Widget):
    """Widget with a value, Wraps ValueWidgetProtocol.

    Parameters
    ----------
    value : Any, optional
        The starting value for the widget, by default ``None``
    bind : Any, optional
        A value or callback to bind this widget, then whenever `widget.value` is
        accessed, the value provided here will be returned.  ``value`` can be a
        callable, in which case ``value(self)`` will be returned (i.e. your callback
        must accept a single parameter, which is this widget instance.).

    """

    _widget: _protocols.ValueWidgetProtocol
    changed: EventEmitter

    def __init__(self, value: Any = None, bind: Any = UNBOUND, **kwargs):
        self._bound_value: Any = bind
        self._call_bound: bool = True
        super().__init__(**kwargs)
        if value is not None:
            self.value = value
        if self._bound_value is not UNBOUND and "visible" not in kwargs:
            self.hide()

    def _post_init(self):
        super()._post_init()
        self.changed = EventEmitter(source=self, type="changed")
        self._widget._mgui_bind_change_callback(
            lambda *x: self.changed(value=x[0] if x else None)
        )

    def get_value(self):
        """Callable version of `self.value`.

        The main API is to use `self.value`, however, this is here in order to provide
        an escape hatch if trying to access the widget's value inside of a callback
        bound to self._bound_value.
        """
        return self._widget._mgui_get_value()

    @property
    def value(self):
        """Return current value of the widget.  This may be interpreted by backends."""
        if self._bound_value is not UNBOUND:
            if callable(self._bound_value) and self._call_bound:
                try:
                    return self._bound_value(self)
                except RecursionError as e:
                    raise RuntimeError(
                        "RecursionError in callback bound to "
                        f"<{self.widget_type!r} name={self.name!r}>. If you need to "
                        "access `widget.value` in your bound callback, use "
                        "`widget.get_value()`"
                    ) from e
            return self._bound_value
        return self.get_value()

    @value.setter
    def value(self, value):
        return self._widget._mgui_set_value(value)

    def __repr__(self) -> str:
        """Return representation of widget of instsance."""
        val = self.value if self._bound_value is UNBOUND else self._bound_value
        if hasattr(self, "_widget"):
            return (
                f"{self.widget_type}(value={val!r}, "
                f"annotation={self.annotation!r}, name={self.name!r})"
            )
        else:
            return f"<Uninitialized {self.widget_type}>"

    def bind(self, value: Any, call: bool = True) -> None:
        """Binds ``value`` to self.value.

        If a value is bound to this widget, then whenever `widget.value` is accessed,
        the value provided here will be returned.  ``value`` can be a callable, in which
        case ``value(self)`` will be returned (i.e. your callback must accept a single
        parameter, which is this widget instance.).

        If you provide a callable and you *don't* want it to be called (but rather just
        returned as a callable object, then use ``call=False`` when binding your value.

        Note: if you need to access the "original" ``widget.value`` within your
        callback, please use ``widget.get_value()`` instead of the ``widget.value``
        property, in order to avoid a RuntimeError.

        Parameters
        ----------
        value : Any
            The value (or callback) to return when accessing this widget's value.
        call : bool, optional
            If ``value`` is a callable and ``call`` is ``True``, the callback will be
            called as ``callback(self)`` when accessing ``self.value``.  If ``False``,
            the callback will simply be returned as a callable object, by default,
            ``True``.
        """
        self._call_bound = call
        self._bound_value = value

    def unbind(self) -> None:
        """Unbinds any bound values. (see ``ValueWidget.bind``)."""
        self._bound_value = UNBOUND
