from magicgui import magicgui


def f(x: int, y="a string") -> str:
    return f"{y} {x}"


def g(x: int = 6, y="another string") -> str:
    return f"{y} asdfsdf {x}"


@magicgui(call_button=True, func={"choices": ["f", "g"]})
def example(func="f"):
    pass


def update(e):
    if len(example) > 2:
        del example[1]
    example.insert(1, magicgui(globals()[e.value]))


example.func.changed.connect(update)
example.show(run=True)
