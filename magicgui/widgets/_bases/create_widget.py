from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from magicgui.application import use_app
from magicgui.widgets import _bases, _protocols

from .widget import Widget

if TYPE_CHECKING:
    from magicgui.types import WidgetOptions


def create_widget(
    value: Any = _bases.value_widget.UNSET,
    annotation: Any = None,
    name: str = "",
    param_kind: str | inspect._ParameterKind = "POSITIONAL_OR_KEYWORD",
    label=None,
    gui_only=False,
    app=None,
    widget_type: str | type[_protocols.WidgetProtocol] | None = None,
    options: WidgetOptions = dict(),
):
    """Create and return appropriate widget subclass.

    This factory function can be used to create a widget appropriate for the
    provided ``value`` and/or ``annotation`` provided.

    Parameters
    ----------
    value : Any, optional
        The starting value for the widget, by default ``None``
    annotation : Any, optional
        The type annotation for the parameter represented by the widget, by default
        ``None``
    name : str, optional
        The name of the parameter represented by this widget. by default ``""``
    param_kind : str, optional
        The :attr:`inspect.Parameter.kind` represented by this widget.  Used in building
        signatures from multiple widgets, by default "``POSITIONAL_OR_KEYWORD``"
    label : str
        A string to use for an associated Label widget (if this widget is being
        shown in a :class:`~magicgui.widgets.Container` widget, and labels are on).
        By default, ``name`` will be used. Note: ``name`` refers the name of the
        parameter, as might be used in a signature, whereas label is just the label
        for that widget in the GUI.
    gui_only : bool, optional
        Whether the widget should be considered "only for the gui", or if it should
        be included in any widget container signatures, by default False
    app : str, optional
        The backend to use, by default ``None``
    widget_type : str or Type[WidgetProtocol] or None
        A class implementing a widget protocol or a string with the name of a
        magicgui widget type (e.g. "Label", "PushButton", etc...).
        If provided, this widget type will be used instead of the type
        autodetermined from ``value`` and/or ``annotation`` above.
    options : WidgetOptions, optional
        Dict of options to pass to the Widget constructor, by default dict()

    Returns
    -------
    Widget
        An instantiated widget subclass

    Raises
    ------
    TypeError
        If the provided or autodetected ``widget_type`` does not implement any known
        widget protocols from widgets._protocols.
    """
    kwargs = locals()
    _kind = kwargs.pop("param_kind", None)
    _app = use_app(kwargs.pop("app"))
    assert _app.native
    if isinstance(widget_type, _protocols.WidgetProtocol):
        wdg_class = kwargs.pop("widget_type")
    else:
        from magicgui.type_map import get_widget_class

        if widget_type:
            options["widget_type"] = widget_type
        wdg_class, opts = get_widget_class(value, annotation, options)

        if issubclass(wdg_class, Widget):
            opts.update(kwargs.pop("options"))
            kwargs.update(opts)
            kwargs.pop("widget_type", None)
            widget = wdg_class(**kwargs)
            if _kind:
                widget.param_kind = _kind
            return widget

    # pick the appropriate subclass for the given protocol
    # order matters
    for p in ("Categorical", "Ranged", "Button", "Value", ""):
        prot = getattr(_protocols, f"{p}WidgetProtocol")
        if isinstance(wdg_class, prot):

            options = kwargs.pop("options", {})
            cls = getattr(_bases, f"{p}Widget")
            widget = cls(widget_type=wdg_class, **kwargs, **options)
            if _kind:
                widget.param_kind = _kind
            return widget

    raise TypeError(f"{wdg_class!r} does not implement any known widget protocols")
