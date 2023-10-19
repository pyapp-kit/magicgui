from magicgui import widgets

dw = widgets.PushButton(text="Hello World!")
tb = widgets.ToolBar()
tb.add_button(text="Hello", icon="mdi:folder")
tb.add_spacer()
tb.add_button(text="World!", icon="mdi:square-edit-outline")

# sb = widgets.StatusBar()
# sb.set_message("Hello Status!")


main = widgets.MainWindow()
main.add_dock_widget(dw)
main.add_tool_bar(tb)
# main.set_status_bar(sb)
main.status_bar.message = "Hello Status!"

main.show(run=True)
