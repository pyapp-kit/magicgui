# type: ignore
from __future__ import annotations

import enum
from typing import ForwardRef, TypeVar
from unittest.mock import Mock, create_autospec

from magicgui import widgets

W = TypeVar("W", bound=widgets.Widget)


def _mock_widget(WidgetType: type[W], **kwargs) -> W:
    """Create a mock widget with the given spec."""
    from magicgui.widgets import protocols

    _proto = WidgetType.__annotations__.get("_widget", None)
    if _proto is None:
        raise TypeError(f"Cannot mock {WidgetType} without a _widget annotation")
    elif isinstance(_proto, (ForwardRef, str)):
        if isinstance(_proto, str):
            _proto = ForwardRef(_proto)
        _proto = _proto._evaluate({"protocols": protocols}, None, frozenset())
    backend_mock = create_autospec(_proto, spec_set=True)
    widget = WidgetType(widget_type=backend_mock, **kwargs)
    backend_mock.assert_called_once_with(parent=None)
    return widget


def test_base_widgtet_protocol(mock_app):
    widget = _mock_widget(widgets.Widget)

    assert widget.__magicgui_app__ is mock_app
    mock = widget._widget

    mock._mgui_get_native_widget.assert_called_once()
    assert widget.native._magic_widget is widget

    mock._mgui_set_tooltip.assert_called_once_with(None)
    mock._mgui_set_enabled.assert_called_once_with(True)
    mock._mgui_bind_parent_change_callback.assert_called_once()

    assert {"enabled", "visible"}.issubset(set(widget.options))
    mock._mgui_get_enabled.assert_called_once()
    mock._mgui_get_visible.assert_called_once()

    for attr in (
        "width",
        "height",
        "min_width",
        "min_height",
        "max_width",
        "max_height",
    ):
        getattr(widget, attr)
        getattr(mock, f"_mgui_get_{attr}").assert_called_once()
        setattr(widget, attr, 1)
        getattr(mock, f"_mgui_set_{attr}").assert_called_once_with(1)

    widget.show(run=True)
    mock._mgui_set_visible.assert_called_once_with(True)
    mock_app._backend._mgui_run.assert_called_once()

    # shown context
    mock._mgui_set_visible.reset_mock()
    assert mock_app._backend._mgui_get_native_app.call_count == 1
    assert mock_app._backend._mgui_run.call_count == 1
    with widget.shown():
        mock._mgui_set_visible.assert_called_with(True)
        assert mock_app._backend._mgui_get_native_app.call_count == 2
    assert mock_app._backend._mgui_run.call_count == 2

    widget.hide()
    mock._mgui_set_visible.assert_called_with(False)

    widget.close()
    mock._mgui_close_widget.assert_called_once()

    widget.render()
    mock._mgui_render.assert_called_once()


def test_base_widget_events(mock_app):
    widget = _mock_widget(widgets.Widget)
    widget._widget._mgui_set_parent.side_effect = widget._emit_parent

    mock = Mock()
    widget.label_changed.connect(mock)
    widget.label = "new_label"
    mock.assert_called_once_with("new_label")

    mock.reset_mock()
    widget.parent_changed.connect(mock)
    widget.parent = "new_parent"
    mock.assert_called_once()


def test_value_widget_protocol(mock_app):
    widget = _mock_widget(widgets.bases.ValueWidget, value=1)
    widget._widget._mgui_set_value.assert_called_once_with(1)

    widget.value
    assert widget._widget._mgui_get_value.call_count == 1
    widget.get_value()
    assert widget._widget._mgui_get_value.call_count == 2

    widget.value = 2
    widget._widget._mgui_set_value.assert_called_with(2)


def test_value_widget_bind(mock_app):
    widget = _mock_widget(widgets.bases.ValueWidget)

    mock = Mock()
    mock.return_value = 3
    widget.bind(mock)
    mock.assert_not_called()
    assert widget.value == 3
    mock.assert_called_once_with(widget)


def test_value_widget_events(mock_app):
    widget = _mock_widget(widgets.bases.ValueWidget, value=1)
    widget._widget._mgui_set_value.side_effect = widget._on_value_change

    change_mock = Mock()
    widget.changed.connect(change_mock)

    widget.value = 2
    change_mock.assert_called_with(2)


def test_categorical_widget_events(mock_app):
    class E(enum.Enum):
        a = 1
        b = 2

    widget = _mock_widget(widgets.bases.CategoricalWidget, choices=E)
    widget._widget._mgui_get_choices.return_value = ("a", "b")
    widget._widget._mgui_set_value.side_effect = widget._on_value_change

    change_mock = Mock()
    widget.changed.connect(change_mock)

    widget.value = E.b
    change_mock.assert_called_with(E.b)
