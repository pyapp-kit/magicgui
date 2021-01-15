import operator
from itertools import zip_longest
from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Iterable,
    Iterator,
    List,
    MutableMapping,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)
from warnings import warn

from magicgui.application import use_app
from magicgui.widgets._bases import ValueWidget
from magicgui.widgets._protocols import TableWidgetProtocol

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd


def _is_collection(obj):
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
        return [[]], [], []
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
        elif not _is_collection(columns):
            raise TypeError(
                f"'columns' must be a collection, " f"{columns!r} was passed"
            )

    if index:
        if not len(index) == nrows:
            raise ValueError(
                f"Shape of passed values is {(nrows, ncols)!r}, "
                f"indices imply {(len(index), 1)!r}"
            )
        if not _is_collection(index):
            raise TypeError(f"'index' must be a collection, {index!r} was passed")
    return index, columns


IndexKey = Union[int, slice]


_KT = TypeVar("_KT")


class Table(ValueWidget, MutableMapping[_KT, list]):
    """A table widget for pandas, numpy, or dict-of-list data."""

    _widget: TableWidgetProtocol

    def __init__(self, value=None) -> None:
        app = use_app()
        assert app.native
        super().__init__(widget_type=app.get_obj("Table"))
        self._data = DataDescriptor(self)
        if value is not None:
            self.value = value

    @property
    def value(self) -> Tuple[List[list], tuple, tuple]:
        """Return current  of the widget."""
        return self.data.to_list(), self.row_headers, self.column_headers

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
        data, index, columns = normalize_table_data(value)
        self.column_headers = columns or range(len(data[0]))  # type:ignore
        self.row_headers = index or range(len(data))  # type: ignore
        for row, data in enumerate(data):
            self._set_row(row, data)

    @property
    def data(self):
        """Return DataDescriptor object for this table."""
        return self._data

    @data.setter
    def data(self, value):
        """Set 2D table data."""
        # TODO: deal with bad shapes
        self._data.__setitem__(slice(None), value)

    def __delitem__(self, key: _KT) -> None:
        """Delete a column from the table."""
        self._del_column(key)

    def __getitem__(self, key: _KT) -> list:
        """Get a column from the table."""
        return self._get_column(key)

    def __setitem__(self, key: _KT, v: list) -> None:
        """Set a column in the table. If `k` doesn't exist, make a new column."""
        self._set_column(key, v)

    def __iter__(self) -> Iterator:
        """Yield column headers."""
        yield from self.column_headers

    def __len__(self) -> int:
        """Return number of columns."""
        return self._widget._mgui_get_column_count()

    def __hash__(self):
        """Make table hashable."""
        return id(self)

    def __repr__(self) -> str:
        """Return string repr."""
        return f"Table(name={self.name!r}, shape={self.shape})"

    @property
    def row_headers(self) -> tuple:
        """Return row headers."""
        nrows = self._widget._mgui_get_column_count()
        return self._widget._mgui_get_row_headers() or tuple(range(nrows))

    @row_headers.setter
    def row_headers(self, headers: Sequence) -> None:
        """Set row headers."""
        self._check_new_headers(headers, axis="row")
        return self._widget._mgui_set_row_headers(headers)

    @property
    def column_headers(self) -> tuple:
        """Return column headers."""
        headers = self._widget._mgui_get_column_headers()
        if not headers:
            ncols = self._widget._mgui_get_column_count()
            headers = tuple(range(ncols))
        return headers

    @column_headers.setter
    def column_headers(self, headers: Sequence) -> None:
        """Set column headers."""
        self._check_new_headers(headers, axis="column")
        return self._widget._mgui_set_column_headers(headers)

    def _check_new_headers(self, headers, *, axis="column"):
        current_headers = getattr(self._widget, f"_mgui_get_{axis}_headers")()
        if current_headers:
            if len(headers) != len(current_headers):
                raise ValueError(
                    f"Length mismatch: Table has {len(current_headers)} {axis}s, "
                    f"new headers have {len(headers)} elements"
                )
        elif len(headers):
            getattr(self._widget, f"_mgui_set_{axis}_count")(len(headers))

    @property
    def shape(self) -> Tuple[int, int]:
        """Return shape of table widget (rows, cols)."""
        return self._widget._mgui_get_row_count(), self._widget._mgui_get_column_count()

    # # Should we allow this?
    # def reshape(self, shape: Tuple[int, int]) -> None:
    #     """Set shape of table widget (rows, cols)."""
    #     try:
    #         r, c = shape[:2]
    #         r = int(r)
    #         c = int(c)
    #     except (ValueError, TypeError):
    #         raise ValueError("'shape' argument must be an iterable of 2 integers")
    #     self._widget._mgui_set_row_count(r)
    #     self._widget._mgui_set_column_count(c)
    #     # TODO: need to truncate extend headers as necessary

    @property
    def size(self) -> int:
        """Return shape of table widget (rows, cols)."""
        return operator.mul(*self.shape)

    def _iter_slice(self, slc, axis):
        yield from range(*slc.indices(self.shape[axis]))

    def _get_cell(self, row: int, col: int) -> Any:
        return self._widget._mgui_get_cell(row, col)

    def _set_cell(self, row: int, col: int, value: Any):
        return self._widget._mgui_set_cell(row, col, value)

    def _get_column(self, col: _KT, rows: slice = slice(None, None, None)) -> list:
        try:
            col_idx = self.column_headers.index(col)
        except ValueError:
            raise KeyError(f"{col!r} is not a valid column header")
        # self._assert_col(col)
        return [self._get_cell(r, col_idx) for r in self._iter_slice(rows, 0)]

    def _set_column(
        self, col: _KT, value: Iterable, rows: slice = slice(None, None, None)
    ):
        if not isinstance(value, Collection):
            raise TypeError(
                f"value to set column data must be iterable. got {type(value)}"
            )
        nrows, ncols = self.shape
        try:
            col_idx = self.column_headers.index(col)
        except ValueError:
            col_idx = ncols
        if col_idx >= ncols:
            # order is important
            new_headers = self.column_headers + (col,)
            self._widget._mgui_set_column_count(ncols + 1)
            # not using column_headers.setter to avoid _check_new_headers call
            self._widget._mgui_set_column_headers(new_headers)

        # TODO: discuss whether it should be an exception if number of rows don't match
        if len(value) > nrows:
            self._widget._mgui_set_row_count(len(value))

        for v, row in zip_longest(value, self._iter_slice(rows, 0)):
            self._set_cell(row, col_idx, v)

    def _del_column(self, col: _KT) -> None:
        try:
            col_idx = self.column_headers.index(col)
        except ValueError:
            raise KeyError(f"{col!r} is not a valid column header")
        return self._widget._mgui_remove_column(col_idx)

    def _get_row(self, row: int, cols: slice = slice(None, None, None)) -> list:
        self._assert_row(row)
        return [self._get_cell(row, c) for c in self._iter_slice(cols, 1)]

    def _set_row(self, row: int, value: list, cols: slice = slice(None, None, None)):
        self._assert_row(row)
        for v, col in zip(value, self._iter_slice(cols, 1)):
            self._set_cell(row, col, v)

    def _assert_row(self, row):
        nrows = self._widget._mgui_get_row_count()
        if row >= nrows:
            raise IndexError(
                f"index {row} is out of bounds for table with {nrows} rows."
            )
        return row

    def _assert_col(self, col):
        ncols = self._widget._mgui_get_column_count()
        if col >= ncols:
            raise IndexError(
                f"column {col} is out of bounds for table with {ncols} columns."
            )
        return col

    def to_dataframe(self) -> "pd.DataFrame":
        """Convert TableData to dataframe."""
        try:
            import pandas

            return pandas.DataFrame(*self.value)
        except ImportError as e:
            raise ImportError(
                "Cannot convert to dataframe without pandas installed"
            ) from e

    def to_dict(self, orient: str = "dict"):
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
        orient = orient.lower()
        if _contains_duplicates(col_head):
            warn("Table column headers are not unique, some columns will be omitted.")
        nrows, ncols = self.shape
        if orient == "dict":
            if _contains_duplicates(row_head):
                warn("Table row headers are not unique, some rows will be omitted.")
            return {
                col_head[c]: {row_head[r]: self._get_cell(r, c) for r in range(nrows)}
                for c in range(ncols)
            }
        if orient == "list":
            return {header: self[header] for header in self.column_headers}
        if orient == "split":
            return {
                "index": row_head,
                "columns": col_head,
                "data": self.data,
            }
        if orient == "records":
            return [
                {col_head[c]: self._get_cell(r, c) for c in range(ncols)}
                for r in range(nrows)
            ]
        if orient == "index":
            if _contains_duplicates(row_head):
                warn("Table row headers are not unique, some rows will be omitted.")
            return {
                row_head[r]: {col_head[c]: self._get_cell(r, c) for c in range(ncols)}
                for r in range(nrows)
            }
        if orient == "series":
            try:
                from pandas import Series

                return {header: Series(self[header]) for header in self.column_headers}
            except ImportError as e:
                raise ImportError("Must install pandas to use to_dict('series')") from e

        raise ValueError(
            "'orient' argument to 'to_dict' must be one of "
            "('dict', list, 'split', 'records', 'index', 'series)"
        )


class DataDescriptor:
    """Object that provides 2D numpy-like indexing for Table data."""

    def __init__(self, obj: "Table") -> None:
        self._obj = obj

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Data for {self._obj!r}>"

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

    def __getitem__(self, idx: Union[IndexKey, Tuple[IndexKey, IndexKey], str]) -> Any:
        """Get index."""
        if isinstance(idx, (int, slice)):
            return self.__getitem__((idx, slice(None)))  # type: ignore
        obj = self._obj
        if isinstance(idx, tuple):
            assert len(idx) == 2, "Table Widget only accepts 2 arguments to __getitem__"
            r_idx, c_idx = idx
            if isinstance(r_idx, int):
                if isinstance(c_idx, int):
                    return obj._get_cell(r_idx, c_idx)
                if isinstance(c_idx, slice):
                    return obj._get_row(r_idx, c_idx)
            elif isinstance(r_idx, slice):
                if isinstance(c_idx, int):
                    return obj._get_column(c_idx, r_idx)
                if isinstance(c_idx, slice):
                    return [obj._get_row(r, c_idx) for r in obj._iter_slice(r_idx, 0)]
        if isinstance(idx, str):
            return obj._get_column(idx)
        raise ValueError(f"Not a valid idx for __getitem__ {idx!r}")

    def __setitem__(
        self, idx: Union[IndexKey, Tuple[IndexKey, IndexKey], str], value: Any
    ) -> None:
        """Set index."""
        if isinstance(idx, (int, slice)):
            return self.__setitem__((idx, slice(None)), value)
        obj = self._obj
        if isinstance(idx, tuple):
            assert len(idx) == 2, "Table Widget only accepts 2 arguments to __setitem__"
            r_idx, c_idx = idx
            if isinstance(r_idx, int):
                if isinstance(c_idx, int):
                    return obj._set_cell(r_idx, c_idx, value)
                if isinstance(c_idx, slice):
                    return obj._set_row(r_idx, value, c_idx)
            elif isinstance(r_idx, slice):
                # handle extended slices
                if r_idx.step and r_idx.step != 1:
                    # TODO: check value is iterable
                    self._assert_extended_slice(r_idx, len(value))
                if isinstance(c_idx, int):
                    return obj._set_column(c_idx, value, r_idx)
                if isinstance(c_idx, slice):
                    # handle extended slices
                    if c_idx.step and c_idx.step != 1:
                        # TODO: check value is iterable
                        self._assert_extended_slice(c_idx, len(value[0]), axis=1)
                    for v, r in zip(value, obj._iter_slice(r_idx, 0)):
                        obj._set_row(r, v, c_idx)
                    return
        if isinstance(idx, str):
            return obj._set_column(idx, value)
        raise ValueError(f"Not a valid idx for __setitem__ {idx!r}")

    def _assert_extended_slice(self, slc: slice, value_len, axis=0):
        slc_len = _range_len(*slc.indices(self._obj.shape[axis]))
        if slc_len != value_len:
            raise ValueError(
                f"attempt to assign sequence of size {value_len} to "
                f"extended slice of size {slc_len} along axis {axis}"
            )

    def to_numpy(self):
        """Return a Numpy representation of the Table.

        Only the values in the Table will be returned, the axes labels will be removed.
        """
        try:
            import numpy

            return numpy.array(self[:])
        except ImportError as e:
            raise ImportError("Cannot convert to numpy without numpy installed") from e

    def to_list(self):
        """Return table data as a list of lists."""
        return self[:]


def _range_len(start, stop, step):
    return (stop - start - 1) // step + 1


def _contains_duplicates(X):
    seen = set()  # type: ignore
    seen_add = seen.add
    for x in X:
        if x in seen or seen_add(x):
            return True
    return False
