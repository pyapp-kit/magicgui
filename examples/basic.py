from magicgui import magicgui
from qtpy.QtWidgets import QApplication

running = True
app = QApplication.instance()
if not app:
    running = False
    app = QApplication([])


@magicgui
def example(arg=1):
    return arg


widget = example.show()


if not running:
    app.exec_()
