from magicgui import event_loop, magicgui


@magicgui
def example(arg=1):
    return arg


with event_loop():
    example.show()
