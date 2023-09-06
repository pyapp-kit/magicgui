"""# Quantities with pint

Pint is a Python package to define, operate and manipulate physical quantities:
the product of a numerical value and a unit of measurement.
It allows arithmetic operations between them and conversions
from and to different units.
https://pint.readthedocs.io/en/stable/
"""
from pint import Quantity

from magicgui import magicgui


@magicgui
def widget(q=Quantity("1 ms")):
    """Widget allowing users to input quantity measurements."""
    print(q)


widget.show(run=True)
