from qtpy.QtWidgets import QApplication

from magicgui import magicgui

running = True
app = QApplication.instance()
if not app:
    running = False
    app = QApplication([])


@magicgui
def example(arg=1):
    return arg


widget = example.Gui(show=True)

if not running:
    app.exec_()
