from typing import Any, Tuple

from ._bases import ValueWidget
from ._concrete import backend_widget


def _is_dataframe(obj) -> bool:
    try:
        import pandas

        pandas.DataFrame.from_dict
        return isinstance(obj, pandas.DataFrame)
    except ImportError:
        return False


def _is_numpy_array(obj) -> bool:
    try:
        import numpy

        return isinstance(obj, numpy.ndarray)
    except ImportError:
        return False


def _from_nested_index_dict(data) -> dict:
    from collections import defaultdict

    new_data: dict = defaultdict(dict)
    for index, s in data.items():
        for col, v in s.items():
            new_data[col][index] = v
    return new_data


def _from_nested_column_dict(data):
    _index = {frozenset(i) for i in data.values()}
    if len(_index) > 1:
        raise ValueError(
            "All row-dicts must have the same keys. "
            "Install pandas for better table-from-dict support."
        )
    index = tuple(sorted(list(_index)[0]))

    new_data = []
    for col, s in data.items():
        new_data.append([s[i] for i in index])
    return list(zip(*new_data)), index


def _from_dict(
    data, orient="columns", dtype=None, columns=None
) -> Tuple[list, tuple, tuple]:
    """Construct _MguiTable from dict of array-like or dicts.

    logic from pandas.DataFrame.from_dict
    """
    try:
        import pandas

        df = pandas.DataFrame.from_dict(
            data, orient=orient, dtype=dtype, columns=columns
        )
        return df.values, tuple(df.index), tuple(df.columns)
    except ImportError:
        pass

    index: tuple = ()
    orient = orient.lower()
    if orient == "index":
        if len(data) > 0:
            # TODO: this is inaccessible, since Table.value still assumes orient=columns
            # but it may not work
            if isinstance(list(data.values())[0], dict):
                data = _from_nested_index_dict(data)
            else:
                data, index = list(data.values()), tuple(data.keys())
    elif orient == "columns":
        if columns is not None:
            raise ValueError("cannot use columns parameter with orient='columns'")

        columns = tuple(data.keys())
        if isinstance(list(data.values())[0], dict):
            data, index = _from_nested_column_dict(data)
        else:
            data = list(zip(*data.values()))

    else:  # pragma: no cover
        raise ValueError("only recognize index or columns for orient")
    return data, index, columns or ()


def _value_to_table_data(value: Any) -> Tuple[list, tuple, tuple]:
    """Convert arbitrary value into appropriate table data format."""
    if isinstance(value, tuple):
        if not len(value) == 3:
            raise ValueError(
                "Tuple data for a table must be len 3 with form (data, index, columns)"
            )
        data, index, columns = value
        data = _value_to_table_data(data)[0]
    elif isinstance(value, dict):
        data, index, columns = _from_dict(value)
    elif _is_dataframe(value):
        df = value
        data, index, columns = df.values, tuple(df.index), tuple(df.columns)
    elif isinstance(value, list) or _is_numpy_array(value):
        data, index, columns = value, (), ()
    else:
        raise TypeError("Table value must be a dict, dataframe, or array")
    if len(data):
        if not index:
            index = tuple(range(len(data)))
        if not columns:
            columns = tuple(range(len(data[0])))
    return data, index, columns


@backend_widget
class Table(ValueWidget):
    """A table widget for pandas, numpy, or dict-of-list data."""

    @property
    def value(self) -> Tuple[list, tuple, tuple]:
        """Return current value of the widget."""
        return self._widget._mgui_get_value()

    @value.setter
    def value(self, value: Any):
        self._widget._mgui_set_value(_value_to_table_data(value))

    def __repr__(self) -> str:
        """Return string repr."""
        return "Table(name={self.name})\n" + repr(self.value)
