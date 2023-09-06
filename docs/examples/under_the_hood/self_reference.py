"""# Self reference magicgui widgets

Widgets created with magicgui can reference themselves, and use the widget API.
"""
from magicgui import magicgui


@magicgui(auto_call=True, width={"max": 800, "min": 100}, x={"widget_type": "Slider"})
def function(width=400, x: int = 50):
    """Example function."""
    # the widget can reference itself, and use the widget API
    function.x.width = width


function.show(run=True)
