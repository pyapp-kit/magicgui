#!/usr/bin/env python

"""Tests for `magicgui` widgets."""
import math
import pytest

from magicgui._qt.widgets import QDoubleSlider, QLogSlider


@pytest.mark.parametrize("SliderClass", [QDoubleSlider, QLogSlider])
def test_slider(qtbot, SliderClass):
    """Test magicgui sliders."""
    slider = SliderClass()
    qtbot.addWidget(slider)
    assert slider.value() == 0  # default slider value is zero
    slider.setValue(math.pi)
    assert math.isclose(slider.value(), math.pi, abs_tol=0.01)
    slider.setMaximum(10)
    slider.setValue(11)  # above maximum allowed value, value will be clipped
    assert math.isclose(slider.value(), 10, abs_tol=1e-07)
