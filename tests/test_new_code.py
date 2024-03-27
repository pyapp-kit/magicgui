from magicgui import magicgui
from enum import Enum
import sys
import io


class Medium(Enum):
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


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

    snells_law.show(run=True)

    # this code gets what is printed to terminal which I made the message box print to terminal
    captured_output = io.StringIO()
    sys.stdout = captured_output
    snells_law()
    sys.stdout = sys.__stdout__
    # print("\nTest: "+capturedOutput.getvalue())

    assert captured_output.getvalue() == "\nQMessageBox text:  Computation Completed!\n"

