from magicgui import magicgui
from enum import Enum


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


combobox_list.show(run=True)
