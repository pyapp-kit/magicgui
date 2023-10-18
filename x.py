from magicgui import widgets

dw = widgets.PushButton(text="Hello World!")
tb = widgets.ToolBar()

main = widgets.MainWindow()
main.add_dock_widget(dw)
main.add_tool_bar(tb)

main.show(run=True)
