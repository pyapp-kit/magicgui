from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Iterable, get_type_hints

try:
    import ipywidgets
    from ipywidgets import widgets as ipywdg
except ImportError as e:
    raise ImportError(
        "magicgui requires ipywidgets to be installed to use the 'ipynb' backend. "
        "Please run `pip install ipywidgets`"
    ) from e


from magicgui.widgets import protocols

if TYPE_CHECKING:
    from magicgui.widgets.bases import Widget


def _pxstr2int(pxstr: int | str) -> int:
    if isinstance(pxstr, int):
        return pxstr
    if isinstance(pxstr, str) and pxstr.endswith("px"):
        return int(pxstr[:-2])
    return int(pxstr)


def _int2pxstr(pxint: int | str) -> str:
    return f"{pxint}px" if isinstance(pxint, int) else pxint


class _IPyWidget(protocols.WidgetProtocol):
    _ipywidget: ipywdg.Widget

    def __init__(
        self,
        wdg_class: type[ipywdg.Widget] | None = None,
        parent: ipywdg.Widget | None = None,
    ):
        if wdg_class is None:
            wdg_class = get_type_hints(self, None, globals()).get("_ipywidget")
        if wdg_class is None:
            raise TypeError("Must provide a valid ipywidget type")
        self._ipywidget = wdg_class()
        # TODO: assign parent

    def _mgui_close_widget(self):
        self._ipywidget.close()

    # `layout.display` will hide and unhide the widget and collapse the space
    # `layout.visibility` will make the widget (in)visible without changing layout
    def _mgui_get_visible(self):
        return self._ipywidget.layout.display != "none"

    def _mgui_set_visible(self, value: bool):
        self._ipywidget.layout.display = "block" if value else "none"

    def _mgui_get_enabled(self) -> bool:
        return not self._ipywidget.disabled

    def _mgui_set_enabled(self, enabled: bool):
        self._ipywidget.disabled = not enabled

    def _mgui_get_parent(self):
        # TODO: how does ipywidgets handle this?
        # return getattr(self._ipywidget, "parent", None)
        raise NotImplementedError(
            "parent not implemented for ipywidgets backend.  Please open an issue"
        )

    def _mgui_set_parent(self, widget):
        # TODO: how does ipywidgets handle this?
        self._ipywidget.parent = widget

    def _mgui_get_native_widget(self) -> ipywdg.Widget:
        return self._ipywidget

    def _mgui_get_root_native_widget(self) -> ipywdg.Widget:
        return self._ipywidget

    def _mgui_get_width(self) -> int:
        # TODO: ipywidgets deals in CSS ... by default width is `None`
        # will this always work with our base Widget assumptions?
        return _pxstr2int(self._ipywidget.layout.width)

    def _mgui_set_width(self, value: int | str) -> None:
        """Set the current width of the widget."""
        self._ipywidget.layout.width = _int2pxstr(value)

    def _mgui_get_min_width(self) -> int:
        return _pxstr2int(self._ipywidget.layout.min_width)

    def _mgui_set_min_width(self, value: int | str):
        self._ipywidget.layout.min_width = _int2pxstr(value)

    def _mgui_get_max_width(self) -> int:
        return _pxstr2int(self._ipywidget.layout.max_width)

    def _mgui_set_max_width(self, value: int | str):
        self._ipywidget.layout.max_width = _int2pxstr(value)

    def _mgui_get_height(self) -> int:
        """Return the current height of the widget."""
        return _pxstr2int(self._ipywidget.layout.height)

    def _mgui_set_height(self, value: int) -> None:
        """Set the current height of the widget."""
        self._ipywidget.layout.height = _int2pxstr(value)

    def _mgui_get_min_height(self) -> int:
        """Get the minimum allowable height of the widget."""
        return _pxstr2int(self._ipywidget.layout.min_height)

    def _mgui_set_min_height(self, value: int) -> None:
        """Set the minimum allowable height of the widget."""
        self._ipywidget.layout.min_height = _int2pxstr(value)

    def _mgui_get_max_height(self) -> int:
        """Get the maximum allowable height of the widget."""
        return _pxstr2int(self._ipywidget.layout.max_height)

    def _mgui_set_max_height(self, value: int) -> None:
        """Set the maximum allowable height of the widget."""
        self._ipywidget.layout.max_height = _int2pxstr(value)

    def _mgui_get_tooltip(self) -> str:
        return self._ipywidget.tooltip

    def _mgui_set_tooltip(self, value: str | None) -> None:
        self._ipywidget.tooltip = value

    def _ipython_display_(self, **kwargs):
        return self._ipywidget._ipython_display_(**kwargs)

    def _mgui_bind_parent_change_callback(self, callback):
        pass

    def _mgui_render(self):
        pass


class EmptyWidget(_IPyWidget):
    _ipywidget: ipywdg.Widget

    def _mgui_get_value(self) -> Any:
        raise NotImplementedError()

    def _mgui_set_value(self, value: Any) -> None:
        raise NotImplementedError()

    def _mgui_bind_change_callback(self, callback: Callable):
        pass


class _IPyValueWidget(_IPyWidget, protocols.ValueWidgetProtocol):
    def _mgui_get_value(self) -> float:
        return self._ipywidget.value

    def _mgui_set_value(self, value: Any) -> None:
        self._ipywidget.value = value

    def _mgui_bind_change_callback(self, callback):
        def _inner(change_dict):
            callback(change_dict.get("new"))

        self._ipywidget.observe(_inner, names=["value"])


class _IPyStringWidget(_IPyValueWidget):
    def _mgui_set_value(self, value) -> None:
        super()._mgui_set_value(str(value))


class _IPyRangedWidget(_IPyValueWidget, protocols.RangedWidgetProtocol):
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

    def _mgui_get_adaptive_step(self) -> bool:
        return False

    def _mgui_set_adaptive_step(self, value: bool):
        # TODO:
        ...
        # raise NotImplementedError('adaptive step not implemented for ipywidgets')


class _IPySupportsOrientation(protocols.SupportsOrientation):
    _ipywidget: ipywdg.Widget

    def _mgui_set_orientation(self, value) -> None:
        self._ipywidget.orientation = value

    def _mgui_get_orientation(self) -> str:
        return self._ipywidget.orientation


class _IPySupportsChoices(protocols.SupportsChoices):
    _ipywidget: ipywdg.Widget

    def _mgui_get_choices(self) -> tuple[tuple[str, Any]]:
        """Get available choices."""
        return self._ipywidget.options

    def _mgui_set_choices(self, choices: Iterable[tuple[str, Any]]) -> None:
        """Set available choices."""
        self._ipywidget.options = choices

    def _mgui_del_choice(self, choice_name: str) -> None:
        """Delete a choice."""
        options = [
            item
            for item in self._ipywidget.options
            if (not isinstance(item, tuple) or item[0] != choice_name)
            and item != choice_name
        ]
        self._ipywidget.options = options

    def _mgui_get_choice(self, choice_name: str) -> Any:
        """Get the data associated with a choice."""
        for item in self._ipywidget.options:
            if isinstance(item, tuple) and item[0] == choice_name:
                return item[1]
            elif item == choice_name:
                return item
        return None

    def _mgui_get_count(self) -> int:
        return len(self._ipywidget.options)

    def _mgui_get_current_choice(self) -> str:
        return self._ipywidget.label

    def _mgui_set_choice(self, choice_name: str, data: Any) -> None:
        """Set the data associated with a choice."""
        self._ipywidget.options = (*self._ipywidget.options, (choice_name, data))


class _IPySupportsText(protocols.SupportsText):
    """Widget that have text (in addition to value)... like buttons."""

    _ipywidget: ipywdg.Widget

    def _mgui_set_text(self, value: str) -> None:
        """Set text."""
        self._ipywidget.description = value

    def _mgui_get_text(self) -> str:
        """Get text."""
        return self._ipywidget.description


class _IPySupportsIcon(protocols.SupportsIcon):
    """Widget that can show an icon."""

    _ipywidget: ipywdg.Button

    def _mgui_set_icon(self, value: str | None, color: str | None) -> None:
        """Set icon."""
        # only ipywdg.Button actually supports icons.
        # but our button protocol allows it for all buttons subclasses
        # so we need this method in the concrete subclasses, but we
        # can't actually set the icon for anything but ipywdg.Button
        if hasattr(self._ipywidget, "icon"):
            # by splitting on ":" we allow for "prefix:icon-name" syntax
            # which works for iconify icons served by qt, while still
            # allowing for bare "icon-name" syntax which works for ipywidgets.
            # note however... only fa4/5 icons will work for ipywidgets.
            value = value or ""
            self._ipywidget.icon = value.replace("fa-", "").split(":", 1)[-1]
            self._ipywidget.style.text_color = color


class _IPyCategoricalWidget(_IPyValueWidget, _IPySupportsChoices):
    pass


class _IPyButtonWidget(_IPyValueWidget, _IPySupportsText, _IPySupportsIcon):
    pass


class _IPySliderWidget(_IPyRangedWidget, _IPySupportsOrientation):
    """Protocol for implementing a slider widget."""

    def __init__(self, readout: bool = True, orientation: str = "horizontal", **kwargs):
        super().__init__(**kwargs)

    def _mgui_set_readout_visibility(self, visible: bool) -> None:
        """Set visibility of readout widget."""
        # TODO

    def _mgui_get_tracking(self) -> bool:
        """If tracking is False, changed is only emitted when released."""
        # TODO
        return True

    def _mgui_set_tracking(self, tracking: bool) -> None:
        """If tracking is False, changed is only emitted when released."""
        # TODO


class Label(_IPyStringWidget):
    _ipywidget: ipywdg.Label


class LineEdit(_IPyStringWidget):
    _ipywidget: ipywdg.Text


class Password(_IPyStringWidget):
    _ipywidget: ipywdg.Password


class LiteralEvalLineEdit(_IPyStringWidget):
    _ipywidget: ipywdg.Text

    def _mgui_get_value(self) -> Any:
        from ast import literal_eval

        value = super()._mgui_get_value()
        return literal_eval(value)  # type: ignore


class TextEdit(_IPyStringWidget):
    _ipywidget: ipywdg.Textarea


class DateEdit(_IPyValueWidget):
    _ipywidget: ipywdg.DatePicker


class DateTimeEdit(_IPyValueWidget):
    _ipywidget: ipywdg.DatetimePicker


class TimeEdit(_IPyValueWidget):
    _ipywidget: ipywdg.TimePicker


class ToolBar(_IPyWidget):
    _ipywidget: ipywidgets.HBox

    def __init__(self, **kwargs):
        super().__init__(ipywidgets.HBox, **kwargs)
        self._icon_sz: tuple[int, int] | None = None

    def _mgui_add_button(self, text: str, icon: str, callback: Callable) -> None:
        """Add an action to the toolbar."""
        btn = ipywdg.Button(
            description=text, icon=icon, layout={"width": "auto", "height": "auto"}
        )
        if callback:
            btn.on_click(lambda e: callback())
        self._add_ipywidget(btn)

    def _add_ipywidget(self, widget: ipywidgets.Widget) -> None:
        children = list(self._ipywidget.children)
        children.append(widget)
        self._ipywidget.children = children

    def _mgui_add_separator(self) -> None:
        """Add a separator line to the toolbar."""
        # Define the vertical separator
        sep = ipywdg.Box(
            layout=ipywdg.Layout(border_left="1px dotted gray", margin="1px 4px")
        )
        self._add_ipywidget(sep)

    def _mgui_add_spacer(self) -> None:
        """Add a spacer to the toolbar."""
        self._add_ipywidget(ipywdg.Box(layout=ipywdg.Layout(flex="1")))

    def _mgui_add_widget(self, widget: Widget) -> None:
        """Add a widget to the toolbar."""
        self._add_ipywidget(widget.native)

    def _mgui_get_icon_size(self) -> tuple[int, int] | None:
        """Return the icon size of the toolbar."""
        return self._icon_sz

    def _mgui_set_icon_size(self, size: int | (tuple[int, int] | None)) -> None:
        """Set the icon size of the toolbar."""
        if isinstance(size, int):
            size = (size, size)
        elif size is None:
            size = (0, 0)
        elif not isinstance(size, tuple):
            raise ValueError("icon size must be an int or tuple of ints")
        sz = max(size)
        self._icon_sz = (sz, sz)
        for child in self._ipywidget.children:
            if hasattr(child, "style"):
                child.style.font_size = f"{sz}px" if sz else None
            child.layout.min_height = f"{sz*2}px" if sz else None

    def _mgui_clear(self) -> None:
        """Clear the toolbar."""
        self._ipywidget.children = ()


class PushButton(_IPyButtonWidget):
    _ipywidget: ipywdg.Button

    def _mgui_bind_change_callback(self, callback):
        self._ipywidget.on_click(lambda e: callback(False))

    # ipywdg.Button does not have any value. Return False for compatibility with Qt.
    def _mgui_get_value(self) -> float:
        return False

    def _mgui_set_value(self, value: Any) -> None:
        pass


class CheckBox(_IPyButtonWidget):
    _ipywidget: ipywdg.Checkbox


class RadioButton(_IPyButtonWidget):
    _ipywidget: ipywidgets.RadioButtons


class SpinBox(_IPyRangedWidget):
    _ipywidget: ipywidgets.IntText


class FloatSpinBox(_IPyRangedWidget):
    _ipywidget: ipywidgets.FloatText


class Slider(_IPySliderWidget):
    _ipywidget: ipywidgets.IntSlider


class FloatSlider(_IPySliderWidget):
    _ipywidget: ipywidgets.FloatSlider


class ComboBox(_IPyCategoricalWidget):
    _ipywidget: ipywidgets.Dropdown


class Select(_IPyCategoricalWidget):
    _ipywidget: ipywidgets.SelectMultiple


# CONTAINER ----------------------------------------------------------------------


class Container(_IPyWidget, protocols.ContainerProtocol, protocols.SupportsOrientation):
    def __init__(self, layout="horizontal", scrollable: bool = False, **kwargs):
        wdg_class = ipywidgets.VBox if layout == "vertical" else ipywidgets.HBox
        super().__init__(wdg_class, **kwargs)

    def _mgui_add_widget(self, widget: Widget) -> None:
        children = list(self._ipywidget.children)
        children.append(widget.native)
        self._ipywidget.children = children
        widget.parent = self._ipywidget

    def _mgui_insert_widget(self, position: int, widget: Widget) -> None:
        children = list(self._ipywidget.children)
        children.insert(position, widget.native)
        self._ipywidget.children = children
        widget.parent = self._ipywidget

    def _mgui_remove_widget(self, widget: Widget) -> None:
        children = list(self._ipywidget.children)
        children.remove(widget.native)
        self._ipywidget.children = children

    def _mgui_remove_index(self, position: int) -> None:
        children = list(self._ipywidget.children)
        children.pop(position)
        self._ipywidget.children = children

    def _mgui_count(self) -> int:
        return len(self._ipywidget.children)

    def _mgui_index(self, widget: Widget) -> int:
        return self._ipywidget.children.index(widget.native)

    def _mgui_get_index(self, index: int) -> Widget | None:
        """(return None instead of index error)."""
        return self._ipywidget.children[index]._magic_widget

    def _mgui_get_native_layout(self) -> Any:
        raise self._ipywidget

    def _mgui_get_margins(self) -> tuple[int, int, int, int]:
        margin = self._ipywidget.layout.margin
        if margin:
            try:
                top, rgt, bot, lft = (int(x.replace("px", "")) for x in margin.split())
                return lft, top, rgt, bot
            except ValueError:
                return margin
        return (0, 0, 0, 0)

    def _mgui_set_margins(self, margins: tuple[int, int, int, int]) -> None:
        lft, top, rgt, bot = margins
        self._ipywidget.layout.margin = f"{top}px {rgt}px {bot}px {lft}px"

    def _mgui_set_orientation(self, value) -> None:
        raise NotImplementedError(
            "Sorry, changing orientation after instantiation "
            "is not yet implemented for ipywidgets."
        )

    def _mgui_get_orientation(self) -> str:
        return "vertical" if isinstance(self._ipywidget, ipywdg.VBox) else "horizontal"


def get_text_width(text):
    # FIXME: how to do this in ipywidgets?
    return 40
