"""# Jupyter notebooks and magicgui

This example shows magicgui widgets embedded in a jupyter notebook.

The key function here is `use_app("ipynb")`.

You can also [get this example at github](https://github.com/pyapp-kit/magicgui/blob/main/docs/examples/notebooks/magicgui_jupyter.ipynb).

```python hl_lines="4-5"
import math
from enum import Enum

from magicgui import magicgui, use_app
use_app("ipynb")

class Medium(Enum):
    # Various media and their refractive indices.
    Glass = 1.520
    Oil = 1.515
    Water = 1.333
    Air = 1.0003


@magicgui(
    call_button="calculate", result_widget=True, layout='vertical', auto_call=True
)
def snells_law(aoi=1.0, n1=Medium.Glass, n2=Medium.Water, degrees=True):
    # Calculate the angle of refraction given two media and an angle of incidence.
    if degrees:
        aoi = math.radians(aoi)
    try:
        n1 = n1.value
        n2 = n2.value
        result = math.asin(n1 * math.sin(aoi) / n2)
        return round(math.degrees(result) if degrees else result, 2)
    except ValueError:  # math domain error
        return "TIR!"


snells_law
```
"""

# %%
# ![magicgui widget embedded in the jupyter notebook](../../images/jupyter_magicgui_widget.png)
