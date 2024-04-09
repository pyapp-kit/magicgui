from magicgui import magicgui
from enum import Enum
import sys
import io

from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


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
    cur_index = getattr(combobox_enum.group, "current_index")
    assert cur_index == 0


def test_combobox_index_enum_select():
    """ selects different combobox option """
    @magicgui(auto_call=True, call_button="get index (enum)")
    def combobox_enum(group: members = members.jared):
        return

    combobox_enum.show(run=False)
    QTest.keyClick(combobox_enum.group.native, Qt.Key_Down)
    cur_index = getattr(combobox_enum.group, "current_index")
    assert cur_index == 1


def test_combobox_index_list():
    @magicgui(group={"choices": ["jared", "james", "graham", "carlvin"]}, auto_call=True, call_button="get index list")
    def combobox_enum(group="jared"):
        return

    combobox_enum.show(run=False)
    cur_index = getattr(combobox_enum.group, "current_index")
    assert cur_index == 0


def test_combobox_index_list_select():
    @magicgui(group={"choices": ["jared", "james", "graham", "carlvin"]}, auto_call=True, call_button="get index list")
    def combobox_enum(group="jared"):
        return

    combobox_enum.show(run=False)
    QTest.keyClick(combobox_enum.group.native, Qt.Key_Down)
    cur_index = getattr(combobox_enum.group, "current_index")
    assert cur_index == 1


