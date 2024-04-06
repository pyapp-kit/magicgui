from magicgui import magicgui
from enum import Enum

class members(Enum):
    jared = "jared"
    james = "james"
    graham = "graham"
    carlvin = "carlvin"

@magicgui(auto_call=True, call_button = "original")
def combobox_original(group: members = members.jared):
    cur_choice = combobox_original.group.current_choice
    current_index = combobox_original.group.current_index
    print(current_index)

    return

combobox_original.show(run=True)
