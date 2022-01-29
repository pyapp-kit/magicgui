from __future__ import annotations

from magicgui import magicgui
from magicgui import widgets as wdt


def test_symple_types():
    @magicgui
    def f(
        i: int,
        s: str,
        f: float,
        b: bool,
        r: range = range(0, 10),
        sl: slice = slice(0, 10),
    ):
        pass

    assert isinstance(f.i, wdt.SpinBox)
    assert isinstance(f.s, wdt.LineEdit)
    assert isinstance(f.f, wdt.FloatSpinBox)
    assert isinstance(f.b, wdt.CheckBox)
    assert isinstance(f.r, wdt.RangeEdit)
    assert isinstance(f.sl, wdt.SliceEdit)
