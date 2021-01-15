from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    List,
    MutableSequence,
    Tuple,
    Union,
    cast,
    overload,
)

from ._bases import ValueWidget
from ._concrete import backend_widget
from ._protocols import TableWidgetProtocol

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


def _from_nested_column_dict(data) -> Tuple[List[list], list]:
    _index = {frozenset(i) for i in data.values()}
    if len(_index) > 1:
        raise ValueError(
            "All row-dicts must have the same keys. "
            "Install pandas for better table-from-dict support."
        )
    index = list(sorted(list(_index)[0]))
    new_data = []
    for col, s in data.items():
        new_data.append([s[i] for i in index])
    return list(list(x) for x in zip(*new_data)), index


def from_dict(data, dtype=None) -> Tuple[List[list], list, list]:
    """Construct _MguiTable from dict of array-like or dicts.

    logic from pandas.DataFrame.from_dict
    """
    # try:
    #     import pandas

    #     df = pandas.DataFrame.from_dict(data, orient="columns", dtype=dtype)
    #     return df.values, df.index, df.columns
    # except ImportError:
    #     pass

    columns = list(data)
    if isinstance(list(data.values())[0], dict):
        data, index = _from_nested_column_dict(data)
    else:
        data = list(list(x) for x in zip(*data.values()))
        index = []
    return data, index, columns


TableData = Union[dict, "pd.DataFrame", list, "np.ndarray", tuple, None]


def normalize_table_data(data: TableData) -> Tuple[List[list], list, list]:
    """Convert data to data, row headers, column headers.

    Any of the following can be used as an argument to ``data``

    .. code-block:: python

        dict_of_dicts = {
            "col_1": {"r1": 3, "r2": 2, "r3": 1, "r4": 0},
            "col_2": {"r2": "b", "r4": "d", "r3": "c", "r1": "a"},
        }
        dict_of_lists = {"col_1": [3, 2, 1, 0], "col_2": ["a", "b", "c", "d"]}
        list_of_lists = [[8, 1, 4], [3, 7, 4]]
        numpy_array = np.random.rand(8, 5)
        pandas_dataframe = pd.DataFrame(...)
        tuple_with_header_info = (list_of_lists, ("r1", "r2"), ("c1", "c2", "c3"))

    Parameters
    ----------
    data : dict, dataframe, list, array, tuple, optional
        valid data , by default None

    Notes
    -----
    - If pandas is installed, any dict format that works with DataFrame.from_dict will
      work
    """
    if data is None:
        return [], [], []
    if isinstance(data, dict):
        return from_dict(data)
    if isinstance(data, tuple):
        data_len = len(data)
        _data = data[0] if data else []
        _index = data[1] if data_len > 1 else []
        _columns = data[2] if data_len > 2 else []
        return _data, _index, _columns
    if _is_dataframe(data):
        data = cast("pd.DataFrame", data)
        return data.values, data.index, data.columns
    if isinstance(data, list) or _is_numpy_array(data):
        # TODO: check list dimensions
        return data, [], []
    raise TypeError(
        f"Table value must be a dict, dataframe, list, or array, got {type(data)}"
    )


def _normalize_indices(data, index=None, columns=None):
    ncols = 0
    nrows = 0
    if data is not None:
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
    return index, columns


@backend_widget
class Table(ValueWidget, MutableSequence):
    """A table widget for pandas, numpy, or dict-of-list data."""

    _widget: TableWidgetProtocol
    Index = Union[int, slice]

    @property
    def value(self) -> Tuple[List[list], list, list]:
        """Return current  of the widget."""
        return self.data, self.row_headers, self.column_headers

    @value.setter
    def value(self, value: Any):
        """Set table data from dict, dataframe, list, or array.

        Any of the following can be used as an argument to ``value``

        .. code-block:: python

            dict_of_dicts = {
                "col_1": {"r1": 3, "r2": 2, "r3": 1, "r4": 0},
                "col_2": {"r2": "b", "r4": "d", "r3": "c", "r1": "a"},
            }
            dict_of_lists = {"col_1": [3, 2, 1, 0], "col_2": ["a", "b", "c", "d"]}
            list_of_lists = [[8, 1, 4], [3, 7, 4]]
            numpy_array = np.random.rand(8, 5)
            pandas_dataframe = pd.DataFrame(...)
            tuple_with_header_info = (list_of_lists, ("r1", "r2"), ("c1", "c2", "c3"))

        Parameters
        ----------
        value : Any
            Complete table data in one of the forms described above. Partial table
            updates are not yet supported
        """
        self.data, self.row_headers, self.column_headers = normalize_table_data(value)

    @property
    def data(self) -> List[list]:
        """Return 2D table data."""
        return self._widget._mgui_get_value()

    @data.setter
    def data(self, values: List[list]) -> None:
        """Set 2D table data."""
        r = len(values)
        try:
            c = len(values[0])
        except TypeError:
            c = 1
        self.shape = (r, c)
        self[:] = values

    @property
    def row_headers(self) -> list:
        """Return row headers."""
        return self._widget._mgui_get_row_headers()

    @row_headers.setter
    def row_headers(self, headers: list) -> None:
        """Set row headers."""
        return self._widget._mgui_set_row_headers(headers)

    @property
    def column_headers(self) -> list:
        """Return column headers."""
        return self._widget._mgui_get_column_headers()

    @column_headers.setter
    def column_headers(self, headers: list) -> None:
        """Set column headers."""
        return self._widget._mgui_set_column_headers(headers)

    @property
    def shape(self) -> Tuple[int, int]:
        """Return shape of table widget (rows, cols)."""
        return self._widget._mgui_get_shape()

    @shape.setter
    def shape(self, shape: Tuple[int, int]) -> None:
        """Set shape of table widget (rows, cols)."""
        try:
            r, c = shape[:2]
        except (ValueError, TypeError):
            raise ValueError("'shape' argument must be an iterable object of len>=2")
        self._widget._mgui_set_row_count(r)
        self._widget._mgui_set_column_count(c)
        # TODO: need to truncate extend headers as necessary

    def __repr__(self) -> str:
        """Return string repr."""
        return f"Table(name={self.name})\n" + repr(self[:])

    # fmt: off
    @overload
    def __getitem__(self, arg: int) -> list: ...  # noqa
    @overload
    def __getitem__(self, arg: slice) -> List[list]: ...  # noqa
    @overload
    def __getitem__(self, arg: Tuple[int, int]) -> Any: ...  # noqa
    @overload
    def __getitem__(self, arg: Tuple[int, slice]) -> list: ...  # noqa
    @overload
    def __getitem__(self, arg: Tuple[slice, int]) -> list: ...  # noqa
    @overload
    def __getitem__(self, arg: Tuple[slice, slice]) -> List[list]: ...  # noqa
    @overload
    def __getitem__(self, arg: str) -> list: ...  # noqa
    # fmt: on

    def __getitem__(self, idx: Union[Index, Tuple[Index, Index], str]) -> Any:
        """Get index."""
        if isinstance(idx, (int, slice)):
            return self.__getitem__((idx, slice(None)))  # type: ignore
        if isinstance(idx, tuple):
            assert len(idx) == 2, "Table Widget only accepts 2 arguments to __getitem__"
            r_idx, c_idx = idx
            if isinstance(r_idx, int):
                if isinstance(c_idx, int):
                    return self._get_cell(r_idx, c_idx)
                if isinstance(c_idx, slice):
                    return self._get_row(r_idx, c_idx)
            elif isinstance(r_idx, slice):
                if isinstance(c_idx, int):
                    return self._get_column(c_idx, r_idx)
                if isinstance(c_idx, slice):
                    return [self._get_row(r, c_idx) for r in self._iter_slice(r_idx, 0)]
        if isinstance(idx, str):
            return self._get_column(idx)
        raise ValueError(f"Not a valid idx for __getitem__ {idx!r}")

    def __setitem__(
        self, idx: Union[Index, Tuple[Index, Index], str], value: Any
    ) -> None:
        """Set index."""
        if isinstance(idx, (int, slice)):
            return self.__setitem__((idx, slice(None)), value)
        if isinstance(idx, tuple):
            assert len(idx) == 2, "Table Widget only accepts 2 arguments to __setitem__"
            r_idx, c_idx = idx
            if isinstance(r_idx, int):
                if isinstance(c_idx, int):
                    return self._set_cell(r_idx, c_idx, value)
                if isinstance(c_idx, slice):
                    return self._set_row(r_idx, value, c_idx)
            elif isinstance(r_idx, slice):
                # handle extended slices
                if r_idx.step and r_idx.step != 1:
                    # TODO: check value is iterable
                    self._assert_extended_slice(r_idx, len(value))
                if isinstance(c_idx, int):
                    return self._set_column(c_idx, value, r_idx)
                if isinstance(c_idx, slice):
                    # handle extended slices
                    if c_idx.step and c_idx.step != 1:
                        # TODO: check value is iterable
                        self._assert_extended_slice(c_idx, len(value[0]), axis=1)
                    for v, r in zip(value, self._iter_slice(r_idx, 0)):
                        self._set_row(r, v, c_idx)
                    return
        if isinstance(idx, str):
            return self._set_column(idx, value)
        raise ValueError(f"Not a valid idx for __setitem__ {idx!r}")

    def _assert_extended_slice(self, slc: slice, value_len, axis=0):
        slc_len = _range_len(*slc.indices(self.shape[axis]))
        if slc_len != value_len:
            raise ValueError(
                f"attempt to assign sequence of size {value_len} to "
                f"extended slice of size {slc_len} along axis {axis}"
            )

    def __delitem__(self, *args):
        """Prevent deletion."""
        raise AttributeError("Cannot delete items from table")

    def _iter_slice(self, slc, axis):
        yield from range(*slc.indices(self.shape[axis]))

    def _get_cell(self, row: int, col: int) -> Any:
        return self._widget._mgui_get_cell(row, col)

    def _get_row(self, row: int, cols: slice = slice(None, None, None)) -> list:
        self._assert_row(row)
        return [self._get_cell(row, c) for c in self._iter_slice(cols, 1)]

    def _get_column(
        self, col: Union[int, str], rows: slice = slice(None, None, None)
    ) -> list:
        if isinstance(col, str):
            try:
                col = self.column_headers.index(col)
            except ValueError:
                raise KeyError(f"{col!r} is not a valid column header")
        self._assert_col(col)
        return [self._get_cell(r, col) for r in self._iter_slice(rows, 0)]

    def _set_cell(self, row: int, col: int, value: Any):
        return self._widget._mgui_set_cell(row, col, value)

    def _set_row(self, row: int, value: list, cols: slice = slice(None, None, None)):
        self._assert_row(row)
        for v, col in zip(value, self._iter_slice(cols, 1)):
            self._set_cell(row, col, v)

    def _set_column(
        self, col: Union[int, str], value: list, rows: slice = slice(None, None, None)
    ):
        ncols = self.shape[1]
        if isinstance(col, str):
            try:
                _col: int = self.column_headers.index(col)
            except ValueError:
                _col = ncols
        else:
            _col = col
        if _col >= ncols:
            self._widget._mgui_set_column_count(ncols + 1)
            self.column_headers.append(col)
        for v, row in zip(value, self._iter_slice(rows, 0)):
            self._set_cell(row, _col, v)

    def _assert_row(self, row):
        nrows = len(self)
        if row >= nrows:
            raise IndexError(
                f"index {row} is out of bounds for table "
                f'with {nrows} row{"s" if nrows > 1 else ""}'
            )
        return row

    def _assert_col(self, col):
        ncols = self.shape[1]
        if col >= ncols:
            # XXX: in pandas this would be a KeyError
            raise IndexError(
                f"column {col} is out of bounds for table "
                f'with {ncols} column{"s" if ncols > 1 else ""}'
            )
        return col

    def __len__(self) -> int:
        """Return the number of rows."""
        return self.shape[0]

    def insert(self, index: int, value: Any) -> None:
        """Insert and append not implemented."""
        raise NotImplementedError("Cannot insert or append to a Table Widget")

    def to_dataframe(self):
        """Convert TableData to dataframe."""
        try:
            import pandas

            return pandas.DataFrame(self.data, self.row_headers, self.column_headers)
        except ImportError as e:
            raise ImportError(
                "Cannot convert to dataframe without pandas installed"
            ) from e

    def to_numpy(self):
        """Return a Numpy representation of the Table.

        Only the values in the Table will be returned, the axes labels will be removed.
        """
        try:
            import numpy

            return numpy.array(self.data)
        except ImportError as e:
            raise ImportError("Cannot convert to numpy without numpy installed") from e

    def to_dict(self, orient="dict"):
        """Convert the Table to a dictionary.

        The type of the key-value pairs can be customized with the parameters
        (see below).

        Parameters
        ----------
        orient : str {'dict', 'list', 'series', 'split', 'records', 'index'}
            Determines the type of the values of the dictionary.

            - 'dict' (default) : dict like {column -> {index -> value}}
            - 'list' : dict like {column -> [values]}
            - 'series' : dict like {column -> Series(values)}
            - 'split' : dict like
            {'index' -> [index], 'columns' -> [columns], 'data' -> [values]}
            - 'records' : list like
            [{column -> value}, ... , {column -> value}]
            - 'index' : dict like {index -> {column -> value}}

        """
        col_head = self.column_headers
        row_head = self.row_headers
        nrows, ncols = self.shape
        if "dict" == orient.lower():
            return {
                col_head[c]: {row_head[r]: self._get_cell(r, c) for r in range(nrows)}
                for c in range(ncols)
            }
        if "list" == orient.lower():
            return {col_head[c]: self._get_column(c) for c in range(ncols)}
        if "series" == orient.lower():
            raise NotImplementedError("to_dict('series') not implemented")
        if "split" == orient.lower():
            return {
                "index": row_head,
                "columns": col_head,
                "data": self.data,
            }
        if "records" == orient.lower():
            return [
                {row_head[r]: self._get_cell(r, c) for r in range(nrows)}
                for c in range(ncols)
            ]
        if "index" == orient.lower():
            return {
                row_head[r]: {col_head[c]: self._get_cell(r, c) for c in range(ncols)}
                for r in range(nrows)
            }
        raise ValueError(
            "'orient' argument to 'to_dict' must be one of "
            "('dict', list, 'split', 'records', 'index')"
        )


def _range_len(start, stop, step):
    return (stop - start - 1) // step + 1
