from magicgui import magicgui


def f(x: int, y="a string") -> str:
    return f"{y} {x}"


@magicgui(call_button=True)
def example(x: int, y: str, func=f):
    print(f(x, y))


example.show(run=True)
