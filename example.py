from magicgui import widgets

main = widgets.MainWindow()

# toolbar
tb = widgets.ToolBar()
tb.add_button(text="Folder", icon="mdi:folder")
tb.add_spacer()
tb.add_button(text="Edit", icon="mdi:square-edit-outline")
main.add_tool_bar(tb)

# status bar
main.status_bar.set_message("Hello Status!", timeout=5000)

# doc widgets
main.add_dock_widget(widgets.PushButton(text="Push me."), area="right")

# menus
file_menu = main.menu_bar.add_menu("File")
assert file_menu is main.menu_bar["File"]  # can also access like this
file_menu.add_action("Open", callback=lambda: print("Open"))
subm = file_menu.add_menu("Submenu")
subm.add_action("Subaction", callback=lambda: print("Subaction"))
subm.add_separator()
subm.add_action("Subaction2", callback=lambda: print("Subaction2"))

main.height = 400
main.show(run=True)
