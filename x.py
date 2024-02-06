from qtpy.QtWidgets import QApplication, QHBoxLayout, QWidget

from magicgui.widgets import Container

app = QApplication([])
dock = Container()


def on_parent_changed(parent):
    print(f"parent_changed: {parent=}, {dock.parent=}")
    if parent is not None:  # and visible etc.
        print("setup")
    else:
        print("cleanup")


dock.native_parent_changed.connect(on_parent_changed)
assert dock.native.parent() is None

wdg = QWidget()
layout = QHBoxLayout(wdg)
print("Setting parent>>>>")
layout.addWidget(dock.native)

# Expected: "parent_changed: parent=<QtViewerDockWidget>, dock.parent=<QtViewerDockWidget>"
# assert dock.parent is not None
assert dock.native.parent() is not None
# Click the close button, or remove the dock programmatically
dock.native.setParent(None)

# Expected: "parent_changed: parent=None, dock.parent=None"
assert dock.native.parent() is None
