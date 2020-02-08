from magicgui import magicgui


@magicgui
def example(a, b="hi", c: float = 1):
    """i have a docstring"""
    print(a + b + str(c))


widget = example.show()

@magicgui
def example2(a, b="hi", c: float = 1):
    """i have a docstring"""
    print(a + b + str(c))


widget2 = example2.show()
