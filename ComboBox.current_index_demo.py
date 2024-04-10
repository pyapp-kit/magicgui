from enum import Enum

from magicgui import magicgui


class members(Enum):
    jared = "jared"
    james = "james"
    graham = "graham"
    carlvin = "carlvin"


# enum demo
@magicgui(auto_call=True, call_button="get index (enum)")
def combobox_enum(group: members = members.jared):
    current_index = combobox_enum.group.current_index
    print(current_index)
    return


@magicgui(group={"choices": ["jared", "james", "graham", "carlvin"]}, auto_call=True, call_button="get index (list)")
def combobox_list(group="jared"):
    current_index = combobox_list.group.current_index
    print(current_index)
    return

@magicgui(group={"choices": ["jared", "james", "graham", "carlvin"]}, auto_call=True, call_button="get index (list) original solution")
def combobox_list_original(group="jared"):
    current_name = combobox_list_original.group.current_choice
    current_index = combobox_list_original.group.choices.index(current_name)
    print(current_index)
    return


#combobox_enum.show(run=True)
combobox_list.show(run=True)
#combobox_list_original.show(run=True)
