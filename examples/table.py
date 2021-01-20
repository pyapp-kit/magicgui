"""Demonstrating a few ways to input tables."""
import numpy as np

from magicgui.widgets import PushButton, Slider, Table

# all of these are valid data types
dict_of_lists = {"col_1": [1, 4], "col_2": [2, 5], "col_3": [3, 6]}
# column-dict-of-row-dicts
dict_of_dict = {
    "col_1": {"r1": 1, "r2": 4},
    "col_2": {"r1": 2, "r2": 5},
    "col_3": {"r1": 3, "r2": 6},
}
# list-of-lists
list_of_list = [[1, 2, 3], [4, 5, 6]]
# Records: List-of-column-dict
list_of_records = [
    {"col_1": 1, "col_2": 2, "col_3": 3},
    {"col_1": 4, "col_2": 5, "col_3": 6},
]

# 3-tuple of data, index, column
data_index_column_tuple = (([[1, 2, 3], [4, 5, 6]], ("r1", "r2"), ("c1", "c2", "c3")),)
# split-dict
split_dict = {
    "data": [[1, 2, 3], [4, 5, 6]],
    "index": ("r1", "r2"),
    "columns": ("c1", "c2", "c3"),
}

table = Table(value=dict_of_lists)

# it behaves like a dict:
table["new_col"] = [5, 5]
assert table.pop("new_col") == [5, 5]
# keys and items have both regular (column) and "row" modes
col_item_view = table.items()  # iterate col_header/column
row_item_view = table.items("row")  # iterate row_header/row

# we can just call dict() to get back our dict of lists
assert dict(table) == dict_of_lists
# or use one of many other exports in `to_dict`
assert table.to_dict("records") == list_of_records

# change headers
table.row_headers = ("row1", "row2")
table.column_headers = ("a", "b", "c")

# setting value clears and resets the table:
table.value = np.arange(18).reshape(6, 3)
# we can get/set/delete the 2D data table using numpy-style indexing:
# get every other row
assert table.data[::2] == [[0, 1, 2], [6, 7, 8], [12, 13, 14]]
# set every other column in the 3rd row
table.data[2, ::2] = [99, 99]

# export to numpy or pandas
# table.data.to_numpy()
# table.to_dataframe()

table.show(run=True)
