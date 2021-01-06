from typing import TYPE_CHECKING, Any, Collection, Optional, Tuple, Union

from ._bases import ValueWidget
from ._concrete import backend_widget

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd


def is_collection(obj):
    """Return True if object is a non-string collection."""
    return isinstance(obj, Collection) and not isinstance(obj, str)


def _is_dataframe(obj) -> bool:
    try:
        import pandas

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


TableValue = Union[dict, "pd.DataFrame", list, "np.ndarray"]


class TableData:
    """Basic representation of 2D data with column and index headers."""

    def __new__(cls, data=None, *args, **kwargs) -> "TableData":
        """Create TableData from dict, dataframe, list, or array."""
        if isinstance(data, dict):
            return TableData.from_dict(data)
        elif _is_dataframe(data):
            return TableData.from_dataframe(data)
        elif isinstance(data, list) or _is_numpy_array(data) or not data:
            return super().__new__(cls)
        raise TypeError("Table value must be a dict, dataframe, list, or array")

    def __init__(
        self,
        data=None,
        index: Optional[Collection] = None,
        columns: Optional[Collection] = None,
    ) -> None:
        ncols = 0
        nrows = 0
        if data:
            nrows = len(data)
            try:
                ncols = len(data[0])
            except TypeError:
                ncols = 1
            if not index:
                index = tuple(range(nrows))
            if not columns:
                columns = tuple(range(ncols))

        if columns:
            if not len(columns) == ncols:
                raise ValueError(
                    f"{len(columns)} columns passed, passed data had {ncols} columns"
                )
            elif not is_collection(columns):
                raise TypeError(
                    f"'columns' must be a collection of some kind, "
                    f"{columns!r} was passed"
                )

        if index:
            if not len(index) == nrows:
                raise ValueError(
                    f"Shape of passed values is {(nrows, ncols)!r}, "
                    f"indices imply {(len(index), 1)!r}"
                )
            if not is_collection(index):
                raise TypeError(
                    f"'index' must be a collection of some kind, {index!r} was passed"
                )

        self.values = data
        self.index = index
        self.columns = columns

    @classmethod
    def from_dataframe(cls, df: "pd.DataFrame") -> "TableData":
        """Convert dataframe value into appropriate table data format."""
        return cls(df.values, tuple(df.index), tuple(df.columns))

    @classmethod
    def from_dict(cls, data, orient="columns", dtype=None, columns=None) -> "TableData":
        """Construct _MguiTable from dict of array-like or dicts.

        logic from pandas.DataFrame.from_dict
        """
        print("from dict")
        try:
            import pandas

            df = pandas.DataFrame.from_dict(
                data, orient=orient, dtype=dtype, columns=columns
            )
            return cls(df.values, tuple(df.index), tuple(df.columns))
        except ImportError:
            pass

        index: tuple = ()
        orient = orient.lower()
        if orient == "index":
            if len(data) > 0:
                # TODO: this is inaccessible, since Table.value still assumes
                # orient=columns ... but it may not work
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
        return cls(data, index, columns)

    def to_dataframe(self):
        """Convert TableData to dataframe."""
        try:
            import pandas

            return pandas.DataFrame(self.values, self.index, self.columns)
        except ImportError as e:
            raise ImportError(
                "Cannot convert to dataframe without pandas installed"
            ) from e


@backend_widget
class Table(ValueWidget):
    """A table widget for pandas, numpy, or dict-of-list data."""

    @property
    def value(self) -> Tuple[list, tuple, tuple]:
        """Return current value of the widget."""
        return self._widget._mgui_get_value()

    @value.setter
    def value(self, value: Any):
        self._widget._mgui_set_value(TableData(value))

    def __repr__(self) -> str:
        """Return string repr."""
        return f"Table(name={self.name})\n" + repr(self.value)
