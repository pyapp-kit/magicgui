from pint import Quantity

from magicgui import magicgui


@magicgui
def widget(q=Quantity("1 ms")):
    print(q)


widget.show(run=True)
