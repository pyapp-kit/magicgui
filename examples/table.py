"""Demonstrating a few ways to input tables."""

import numpy as np

from magicgui import widgets

# table from numpy array
numpy_data = np.random.randint(0, 10, (4, 3))
table1 = widgets.Table(value=numpy_data)

# table from dict of lists (column orientation: keys are column names)
data2 = {"col_1": [3, 2, 1, 0], "col_2": ["a", "b", "c", "d"]}
table2 = widgets.Table(value=data2)


# table from dict of dicts
# (column orientation: keys are column names, subkeys are row names)
data3 = {
    "col_1": {"r1": 3, "r2": 2, "r3": 1, "r4": 0},
    "col_2": {"r2": "b", "r4": "d", "r3": "c", "r1": "a"},
}
table3 = widgets.Table(value=data3)

# table from list of lists
table4 = widgets.Table(value=numpy_data.tolist())

# table from list of lists with index and column names provided
table5 = widgets.Table(
    value=(numpy_data.tolist(), ("r1", "r2", "r3", "r4"), ("c1", "c2", "c3"))
)


try:
    # table from pandas dataframe
    import pandas as pd

    table6 = widgets.Table(value=pd.DataFrame.from_dict(data2))
    table6.show()
except ImportError:
    pass

table1.show()
table2.show()
table3.show()
table4.show()
table5.show(run=True)
