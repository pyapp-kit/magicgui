from magicgui import widgets

dw = widgets.PushButton(text="Hello World!")
tb = widgets.ToolBar()
tb.add_button(text="Hello", icon="mdi:folder")
tb.add_spacer()
tb.add_button(text="World!", icon="mdi:square-edit-outline")


main = widgets.MainWindow()
main.add_dock_widget(dw)
main.add_tool_bar(tb)

# sb = widgets.StatusBar()
# sb.set_message("Hello Status!")
# main.set_status_bar(sb)
# or
main.status_bar.set_message("")

file = main.menu_bar.add_menu("File")
main.menu_bar["File"].add_action("Open", callback=lambda: print("Open"))
assert file is main.menu_bar["File"]
subm = file.add_menu("Submenu")
subm.add_action("Subaction", callback=lambda: print("Subaction"))
subm.add_separator()
subm.add_action("Subaction2", callback=lambda: print("Subaction2"))


main.show(run=True)
