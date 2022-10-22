from typing import Any, Callable, Iterable, Optional, Tuple, Type, Union

try:
    import ipywidgets
    from ipywidgets import widgets as ipywdg
except ImportError as e:
    raise ImportError(
        "magicgui requires ipywidgets to be installed to use the 'ipynb' backend. "
        "Please run `pip install ipywidgets`"
    ) from e

from magicgui.widgets import _protocols
from magicgui.widgets._bases import Widget


def _pxstr2int(pxstr: Union[int, str]) -> int:
    if isinstance(pxstr, int):
        return pxstr
    if isinstance(pxstr, str) and pxstr.endswith("px"):
        return int(pxstr[:-2])
    return int(pxstr)


def _int2pxstr(pxint: Union[int, str]) -> str:
    return f"{pxint}px" if isinstance(pxint, int) else pxint


class _IPyWidget(_protocols.WidgetProtocol):
    _ipywidget: ipywdg.Widget

    def __init__(
        self,
        wdg_class: Type[ipywdg.Widget] = None,
        parent: Optional[ipywdg.Widget] = None,
    ):
        if wdg_class is None:
            wdg_class = type(self).__annotations__.get("_ipywidget")
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
        return getattr(self._ipywidget, "parent", None)

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

    def _mgui_set_width(self, value: Union[int, str]) -> None:
        """Set the current width of the widget."""
        self._ipywidget.layout.width = _int2pxstr(value)

    def _mgui_get_min_width(self) -> int:
        return _pxstr2int(self._ipywidget.layout.min_width)

    def _mgui_set_min_width(self, value: Union[int, str]):
        self._ipywidget.layout.min_width = _int2pxstr(value)

    def _mgui_get_max_width(self) -> int:
        return _pxstr2int(self._ipywidget.layout.max_width)

    def _mgui_set_max_width(self, value: Union[int, str]):
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

    def _mgui_set_tooltip(self, value: Optional[str]) -> None:
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


class _IPyValueWidget(_IPyWidget, _protocols.ValueWidgetProtocol):
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


class _IPyRangedWidget(_IPyValueWidget, _protocols.RangedWidgetProtocol):
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


class _IPySupportsOrientation(_protocols.SupportsOrientation):
    _ipywidget: ipywdg.Widget

    def _mgui_set_orientation(self, value) -> None:
        self._ipywidget.orientation = value

    def _mgui_get_orientation(self) -> str:
        return self._ipywidget.orientation


class _IPySupportsChoices(_protocols.SupportsChoices):
    _ipywidget: ipywdg.Widget

    def _mgui_get_choices(self) -> Tuple[Tuple[str, Any]]:
        """Get available choices."""
        return self._ipywidget.options

    def _mgui_set_choices(self, choices: Iterable[Tuple[str, Any]]) -> None:
        """Set available choices."""
        self._ipywidget.options = choices

    def _mgui_del_choice(self, choice_name: str) -> None:
        """Delete a choice."""
        options = [
            item
            for item in self._ipywidget.options
            if (not isinstance(item, tuple) or item[0] != choice_name)
            and item != choice_name  # noqa: W503
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
        self._ipywidget.options = self._ipywidget.options + ((choice_name, data),)


class _IPySupportsText(_protocols.SupportsText):
    """Widget that have text (in addition to value)... like buttons."""

    _ipywidget: ipywdg.Widget

    def _mgui_set_text(self, value: str) -> None:
        """Set text."""
        self._ipywidget.description = value

    def _mgui_get_text(self) -> str:
        """Get text."""
        return self._ipywidget.description


class _IPyCategoricalWidget(_IPyValueWidget, _IPySupportsChoices):
    pass


class _IPyButtonWidget(_IPyValueWidget, _IPySupportsText):
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

    def _mgui_set_tracking(self, tracking: bool) -> None:
        """If tracking is False, changed is only emitted when released."""
        # TODO


class Label(_IPyStringWidget):
    _ipywidget: ipywdg.Label


class LineEdit(_IPyStringWidget):
    _ipywidget: ipywdg.Text


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


class Container(
    _IPyWidget, _protocols.ContainerProtocol, _protocols.SupportsOrientation
):
    def __init__(self, layout="horizontal", scrollable: bool = False, **kwargs):
        wdg_class = ipywidgets.VBox if layout == "vertical" else ipywidgets.HBox
        super().__init__(wdg_class, **kwargs)

    def _mgui_add_widget(self, widget: "Widget") -> None:
        children = list(self._ipywidget.children)
        children.append(widget.native)
        self._ipywidget.children = children
        widget.parent = self._ipywidget

    def _mgui_insert_widget(self, position: int, widget: "Widget") -> None:
        children = list(self._ipywidget.children)
        children.insert(position, widget.native)
        self._ipywidget.children = children
        widget.parent = self._ipywidget

    def _mgui_remove_widget(self, widget: "Widget") -> None:
        children = list(self._ipywidget.children)
        children.remove(widget.native)
        self._ipywidget.children = children

    def _mgui_remove_index(self, position: int) -> None:
        children = list(self._ipywidget.children)
        children.pop(position)
        self._ipywidget.children = children

    def _mgui_count(self) -> int:
        return len(self._ipywidget.children)

    def _mgui_index(self, widget: "Widget") -> int:
        return self._ipywidget.children.index(widget.native)

    def _mgui_get_index(self, index: int) -> Optional[Widget]:
        """(return None instead of index error)."""
        return self._ipywidget.children[index]._magic_widget

    def _mgui_get_native_layout(self) -> Any:
        raise self._ipywidget

    def _mgui_get_margins(self) -> Tuple[int, int, int, int]:
        margin = self._ipywidget.layout.margin
        if margin:
            try:
                top, rgt, bot, lft = (int(x.replace("px", "")) for x in margin.split())
                return lft, top, rgt, bot
            except ValueError:
                return margin
        return (0, 0, 0, 0)

    def _mgui_set_margins(self, margins: Tuple[int, int, int, int]) -> None:
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
