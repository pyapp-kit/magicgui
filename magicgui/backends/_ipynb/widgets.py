from typing import Any, Iterable, Optional, Tuple, Union

import ipywidgets
from ipywidgets import widgets as ipywdg

from magicgui.widgets import _protocols
from magicgui.widgets._bases import Widget


class _IPyWidget(_protocols.WidgetProtocol):
    _ipywidget: ipywdg.Widget

    def __init__(self, qwidg: ipywdg.Widget):
        self._ipywidget = qwidg()

    # `layout.display` will hide and unhide the widget and collapse the space
    # `layout.visibility` will make the widget (in)visible without changing layout
    def _mgui_hide_widget(self):
        self._ipywidget.layout.display = "none"

    def _mgui_show_widget(self):
        self._ipywidget.layout.display = "block"

    def _mgui_get_enabled(self):
        return not self._ipywidget.disabled

    def _mgui_set_enabled(self, enabled):
        self._ipywidget.disabled = not enabled

    def _mgui_get_native_widget(self):
        return self._ipywidget

    def _mgui_get_width(self):
        # TODO: ipywidgets deals in CSS ... by default width is `None`
        # will this always work with our base Widget assumptions?
        width = self._ipywidget.layout.width
        if isinstance(width, str) and width.endswith("px"):
            return int(width[:-2])
        return None

    def _mgui_set_min_width(self, value: Union[int, str]):
        if isinstance(value, int):
            value = f"{value}px"
        self._ipywidget.layout.min_width = value

    def _ipython_display_(self, **kwargs):
        return self._ipywidget._ipython_display_(**kwargs)

    def _mgui_get_parent(self):
        # TODO: how does ipywidgets handle this?
        return getattr(self._ipywidget, "parent", None)

    def _mgui_set_parent(self, widget):
        # TODO: how does ipywidgets handle this?
        self._ipywidget.parent = widget

    def _mgui_bind_parent_change_callback(self, callback):
        pass

    def _mgui_render(self):
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


class Label(_IPyStringWidget):
    def __init__(self):
        super().__init__(ipywdg.Label)


class LineEdit(_IPyStringWidget):
    def __init__(self):
        super().__init__(ipywdg.Text)


class TextEdit(_IPyStringWidget):
    def __init__(self):
        super().__init__(ipywdg.Textarea)


# class DateTimeEdit(_IPyValueWidget):
#     def __init__(self):
#         super().__init__(?)


class PushButton(_IPyButtonWidget):
    def __init__(self):
        super().__init__(ipywdg.Button)

    def _mgui_bind_change_callback(self, callback):
        self._ipywidget.on_click(lambda e: callback())


class CheckBox(_IPyButtonWidget):
    def __init__(self):
        super().__init__(ipywdg.Checkbox)


class RadioButton(_IPyButtonWidget):
    def __init__(self):
        super().__init__(ipywdg.RadioButtons)


class SpinBox(_IPyRangedWidget):
    def __init__(self):
        super().__init__(ipywdg.IntText)


class FloatSpinBox(_IPyRangedWidget):
    def __init__(self):
        super().__init__(ipywdg.FloatText)


class Slider(_IPySliderWidget):
    def __init__(self):
        super().__init__(ipywdg.IntSlider)


class FloatSlider(_IPySliderWidget):
    def __init__(self):
        super().__init__(ipywdg.FloatSlider)


class ComboBox(_IPyCategoricalWidget):
    def __init__(self):
        super().__init__(ipywidgets.Dropdown)


# CONTAINER ----------------------------------------------------------------------


class Container(
    _IPyWidget, _protocols.ContainerProtocol, _protocols.SupportsOrientation
):
    def __init__(self, layout="horizontal"):
        super().__init__(ipywidgets.VBox if layout == "vertical" else ipywidgets.HBox)

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
