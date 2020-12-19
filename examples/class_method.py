"""Demonstrates decorating a method.

Once the class is instantiated, `instance.method_name` will return a FunctionGui
in which the instance will always be provided as the first argument (i.e. "self") when
the FunctionGui or method is called.
"""
from magicgui import event_loop, magicgui
from magicgui.widgets import Container


class MyObject:
    def __init__(self, name):
        self.name = name
        self.counter = 0.0

    @magicgui(auto_call=True)
    def method(self, sigma: float = 0):
        print(f"instance: {self.name}, counter: {self.counter}, sigma: {sigma}")
        self.counter = self.counter + sigma
        return self.name


with event_loop():
    a = MyObject("a")
    b = MyObject("b")
    container = Container(widgets=[a.method, b.method])
    container.show()
    assert a.method() == "a"
    assert b.method() == "b"
