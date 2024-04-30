import io
import sys
from enum import Enum

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication

from magicgui import magicgui
from magicgui.backends._qtpy import widgets


class Medium(Enum):
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003

class members(Enum):
    jared = "jared"
    james = "james"
    graham = "graham"
    carlvin = "carlvin"


def test_message_box_text():
    @magicgui(call_button="calculate(test)", result_widget=True)
    def snells_law(aoi=30.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
        import math

        aoi = math.radians(aoi) if degrees else aoi
        try:
            result = math.asin(n1.value * math.sin(aoi) / n2.value)
            return math.degrees(result) if degrees else result
        except ValueError:
            return "Total internal reflection"

    snells_law.show(run=False)
    button_widget = getattr(snells_law, '_call_button', None)
    QTest.mouseRelease(button_widget.native, Qt.LeftButton)
    snells_law.close()
    QApplication.quit()


    # this code gets what is printed to terminal which I made the message box print to terminal
    captured_output = io.StringIO()
    sys.stdout = captured_output
    snells_law()
    sys.stdout = sys.__stdout__
    # print("\nTest: "+capturedOutput.getvalue())

    assert captured_output.getvalue() == "\nQMessageBox text:  Computation Completed!\n"


def test_combobox_index_enum():
    @magicgui(auto_call=True, call_button="get index (enum)")
    def combobox_enum(group: members = members.jared):
        return

    combobox_enum.show(run=False)
    cur_index = combobox_enum.group.current_index
    assert cur_index == 0


def test_combobox_index_enum_select():
    """ selects different combobox option """
    @magicgui(auto_call=True, call_button="get index (enum)")
    def combobox_enum(group: members = members.jared):
        return

    combobox_enum.show(run=False)
    QTest.keyClick(combobox_enum.group.native, Qt.Key_Down)
    cur_index = combobox_enum.group.current_index
    assert cur_index == 1


def test_combobox_index_list():
    @magicgui(group={"choices": ["jared", "james", "graham", "carlvin"]}, auto_call=True, call_button="get index list")
    def combobox_enum(group="jared"):
        return

    combobox_enum.show(run=False)
    cur_index = combobox_enum.group.current_index
    assert cur_index == 0


def test_combobox_index_list_select():
    @magicgui(group={"choices": ["jared", "james", "graham", "carlvin"]}, auto_call=True, call_button="get index list")
    def combobox_enum(group="jared"):
        return

    combobox_enum.show(run=False)
    QTest.keyClick(combobox_enum.group.native, Qt.Key_Down)
    cur_index = combobox_enum.group.current_index
    assert cur_index == 1


def test_window_title():
    @magicgui(call_button="calculate(test)", result_widget=True)
    def example_function(aoi=30.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
        import math

        aoi = math.radians(aoi) if degrees else aoi
        try:
            result = math.asin(n1.value * math.sin(aoi) / n2.value)
            return math.degrees(result) if degrees else result
        except ValueError:
            return "Total internal reflection"

    assert example_function._widget._mgui_get_window_title() == 'example_function'


#select widget test
def test_select_checkbox():
    @magicgui(
        pick_some={
            "choices": ("first", "second", "third", "fourth"),
            "allow_multiple": True,
        }
    )
    def my_widget(pick_some=("first")):
        """Dropdown selection function."""


    my_widget.show(run=False)
    list = my_widget.pick_some.native
    assert not list.item(0).isSelected()
    assert list.item(0).checkState() == Qt.Unchecked
    list.item(0).setCheckState(Qt.Checked)
    assert list.item(0).isSelected()
    assert list.item(0).checkState() == Qt.Checked


def test_slider_step():
    @magicgui(auto_call=True, slider_int={"label": "val = 500", "widget_type": "Slider", "value": 500, "min": 400,
                                          "max": 1000, "step": 100}, )
    def widget_slider(slider_int=500, ):
        widget_slider.slider_int.label = "val = " + str(slider_int)
        return slider_int

    widget_slider.show(run=False)

    QTest.keyClick(widget_slider.native, Qt.Key_Right)
    position0 = widgets.slider_values[0]
    position1 = widgets.slider_values[1]
    assert (position1 - position0) == 100


def test_configurable_labels():
    @magicgui(x={"label": "TEST", "label_min_width": 100, "label_min_height": 100, "label_max_width": 200,
                 "label_max_height": 200})
    def example(x="test"):
        return x

    example.show(run=False)

    label_widget = example.x.native
    label_width = label_widget.width()
    label_height = label_widget.height()

    assert label_width > 100
    assert label_width < 200
    assert label_height > 100
    assert label_height < 200




