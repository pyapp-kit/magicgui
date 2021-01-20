import operator
from itertools import zip_longest
from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Dict,
    Generic,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)
from warnings import warn

from typing_extensions import Literal

from magicgui.application import use_app
from magicgui.widgets._bases import Widget
from magicgui.widgets._protocols import TableWidgetProtocol

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd


TblKey = Any
_KT = TypeVar("_KT")  # Key type
_KT_co = TypeVar("_KT_co", covariant=True)  # Key type covariant containers.
_VT_co = TypeVar("_VT_co", covariant=True)  # Value type covariant containers.
TableData = Union[dict, "pd.DataFrame", list, "np.ndarray", tuple, None]
IndexKey = Union[int, slice]


def normalize_table_data(data: TableData) -> Tuple[List[list], list, list]:
    """Convert data to data, row headers, column headers.

    Parameters
    ----------
    data : dict, dataframe, list, array, tuple, optional
        Table data (and/or header data), in one of the accepted formats:

        - list or list-of-lists : [column_values] or [[row_vals], ..., [row_vals]]
        - dict-of-dicts : {column_header -> {row_header -> value}}
        - dict-of-lists : {column_header -> [column_values]}
        - list-of-row-records :
            [{column_headers -> value}, ... , {column_headers -> value}]
        - split-dict-of-lists :
            {'data' -> [values], 'index' -> [index], 'columns' -> [columns]}
        - tuple-of-values : ([values], [row_headers], [column_headers])
        - dict-of-pandas-series : {column_header -> Series(values)}

    """
    if data is None:
        return [], [], []
    if isinstance(data, dict):
        return _from_dict(data)
    if isinstance(data, tuple):
        data_len = len(data)
        _data = data[0] if data else []
        _index = data[1] if data_len > 1 else []
        _columns = data[2] if data_len > 2 else []
        return _data, _index, _columns
    if _is_dataframe(data):
        data = cast("pd.DataFrame", data)
        return data.values, data.index, data.columns
    if isinstance(data, list):
        if data:
            if isinstance(data[0], dict):
                return _from_records(data)
            if not isinstance(data[0], Collection):
                # single column dataset
                return [[i] for i in data], [], []
        return data, [], []
    if _is_numpy_array(data):
        return data, [], []
    raise TypeError(
        f"Table value must be a dict, dataframe, list, or array, got {type(data)}"
    )


class HeadersView(KeysView[_KT]):
    """dictionary view for Table headers."""

    def __init__(self, mapping: "Table", axis: str = "column") -> None:
        super().__init__(mapping)
        self._mapping = mapping
        axis = axis.rstrip("s")
        assert axis in {"row", "column"}, "keys axis must be either 'column' or 'row'"
        self._axis = axis

    def __iter__(self) -> Iterator[_KT_co]:
        """Yield headers."""
        yield from getattr(self._mapping, f"{self._axis}_headers")

    def __repr__(self) -> str:
        """Return string repr of column headers view."""
        return f"{self._axis}_headers({list(self)})"


class TableItemsView(ItemsView[_KT_co, _VT_co], Generic[_KT_co, _VT_co]):
    """dictionary view for Table items."""

    def __init__(self, mapping: Mapping[_KT_co, _VT_co], axis: str = "column") -> None:
        super().__init__(mapping)
        self._mapping: "Table" = mapping  # type: ignore
        axis = axis.rstrip("s")
        assert axis in {"row", "column"}, "keys axis must be either 'column' or 'row'"
        self._axis = axis

    def __iter__(self) -> Iterator[Tuple[_KT_co, _VT_co]]:
        """Yield items."""
        for header in getattr(self._mapping, f"{self._axis}_headers"):
            val = getattr(self._mapping, f"_get_{self._axis}")(header)
            yield (header, val)

    def __repr__(self) -> str:
        """Return string repr of column headers view."""
        n = self._mapping.shape[0 if self._axis == "row" else 1]
        return f"table_items({n} {self._axis}s)"


class Table(Widget, MutableMapping[TblKey, list]):
    """A table widget representing columnar or 2D data with headers.

    Tables behave like plain `dicts`, where the keys are column headers and the
    (list-like) values are column data.

    Parameters
    ----------
    value : dict, dataframe, list, array, tuple, optional
        Table data (and/or header data), in one of the accepted formats:

        - list or list-of-lists : [column_values] or [[row_vals], ..., [row_vals]]
        - dict-of-dicts : {column_header -> {row_header -> value}}
        - dict-of-lists : {column_header -> [column_values]}
        - list-of-row-records :
            [{column_headers -> value}, ... , {column_headers -> value}]
        - split-dict-of-lists :
            {'data' -> [values], 'index' -> [index], 'columns' -> [columns]}
        - tuple-of-values : ([values], [row_headers], [column_headers])
        - dict-of-pandas-series : {column_header -> Series(values)}

    index : Collection, optional
        A sized iterable container of row headers. By default, row headers will be
        ``tuple(range(len(data)))``.  Values provided here override any implied in
        ``value``.
    columns : Collection, optional
        A sized iterable container of column headers. By default, column headers will be
        ``tuple(range(len(data[0])))``.  Values provided here override any implied in
        ``value``.
    **kwargs
        Additional kwargs will be passed to the :class:`magicgui.widgets.Widget`
        constructor.

    Attributes
    ----------
    value : dict
        Returns a dict with the keys `data`, `index`, and `columns` ... representing the
        2D (list of lists) tabular data, row headers, and column headers, respectively.
        If set, will clear and update the table using the new data.
    data : :class:`DataView`
        A :class:`DataView` instance that provides numpy-like indexing (with
        get/set/delete) onto the 2D data array,  For example `table.data[0,2]` gets the
        data in the cell of the first row, 3rd column.  Works with numpy slice syntax.
    column_headers : tuple
        The current column headers.  Can be set with a new sequence to change
    row_headers : tuple
        The current row headers.  Can be set with a new sequence to change
    shape : tuple of int
        The shape of the table in ``(rows, columns)``.
    size : int
        The number of cells in the table.

    Methods
    -------
    keys(axis='column')
        Return a :class:`TableHeadersView`, providing a view on this table's headers.
        Use ``axis='row'`` for row headers.
    items(axis='column')
        Return a :class:`TableItemsView`, providing a view on this table's items, as
        2-tuples of ``(header, data)``. Use ``axis='row'`` for
        ``(row_header, row_data)``
    clear()
        Clear all table data and headers.
    to_dataframe()
        Returns a pandas dataframe representation of this table. (requires pandas)
    to_dict(orient='dict')
        Return one of many different dict-like representations of table and header data.
        See docstring of :meth:`to_dict` for details.
    """

    _widget: TableWidgetProtocol

    def __new__(
        cls,
        value: Optional[TableData] = None,
        *,
        index: Collection = None,
        columns: Collection = None,
        **kwargs,
    ):
        """Just for the signature."""
        return super().__new__(cls)

    def __init__(
        self,
        value: Optional[TableData] = None,
        *,
        index: Collection = None,
        columns: Collection = None,
        **kwargs,
    ) -> None:
        app = use_app()
        assert app.native
        kwargs["widget_type"] = app.get_obj("Table")
        super().__init__(**kwargs)
        self._data = DataView(self)
        data, _index, _columns = normalize_table_data(value)
        self.value = {
            "data": data,
            "index": index if index is not None else _index,
            "columns": columns if columns is not None else _columns,
        }

    @property
    def value(self) -> Dict[TblKey, Collection]:
        """Return dict with current `data`, `index`, and `columns` of the widget."""
        return self.to_dict("split")

    @value.setter
    def value(self, value: TableData):
        """Set table data from dict, dataframe, list, or array.

        Parameters
        ----------
        value : Any
            Complete table data in one of the forms described above. Partial table
            updates are not yet supported
        """
        data, index, columns = normalize_table_data(value)
        _validate_table_data(data, index, columns)
        self.clear()
        try:
            nc = len(data[0])
        except (TypeError, IndexError):
            nc = 0
        self.column_headers = tuple(columns) or range(nc)  # type:ignore
        self.row_headers = tuple(index) or range(len(data))  # type: ignore
        for row, data in enumerate(data):
            self._set_rowi(row, data)

    @property
    def data(self) -> "DataView":
        """Return DataView object for this table."""
        return self._data

    @data.setter
    def data(self, value):
        """Set 2D table data."""
        self._data.__setitem__(slice(None), value)

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

    @property
    def row_headers(self) -> tuple:
        """Return row headers."""
        nrows = self._widget._mgui_get_row_count()
        return self._widget._mgui_get_row_headers() or tuple(range(nrows))

    @row_headers.setter
    def row_headers(self, headers: Sequence) -> None:
        """Set row headers."""
        self._check_new_headers(headers, axis="row")
        return self._widget._mgui_set_row_headers(headers)

    @property
    def shape(self) -> Tuple[int, int]:
        """Return shape of table widget (rows, cols)."""
        return self._widget._mgui_get_row_count(), self._widget._mgui_get_column_count()

    # # Should we allow this?
    # @shape.setter
    # def shape(self, shape: Tuple[int, int]) -> None:
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

    def keys(self, axis: str = "column") -> HeadersView[TblKey]:
        """Return a set-like object providing a view on this table's headers."""
        return HeadersView(self, axis)

    def items(self, axis: str = "column") -> TableItemsView[TblKey, list]:
        """Return a set-like object providing a view on this table's items."""
        return TableItemsView(self, axis)

    def clear(self):
        """Clear the table."""
        self._widget._mgui_set_row_count(0)
        self._widget._mgui_set_column_count(0)

    def __delitem__(self, key: TblKey) -> None:
        """Delete a column from the table."""
        self._del_column(key)

    def __getitem__(self, key: TblKey) -> list:
        """Get a column from the table."""
        return self._get_column(key)

    def __setitem__(self, key: TblKey, v: list) -> None:
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
        name = f"name={self.name!r}, " if self.name else ""
        return f"Table({name}shape={self.shape} at {hex(id(self))})"

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

    def _iter_slice(self, slc, axis):
        yield from range(*slc.indices(self.shape[axis]))

    def _get_cell(self, row: int, col: int) -> Any:
        return self._widget._mgui_get_cell(row, col)

    def _set_cell(self, row: int, col: int, value: Any):
        return self._widget._mgui_set_cell(row, col, value)

    def _get_column(self, col: TblKey, rows: slice = slice(None)) -> list:
        try:
            col_idx = self.column_headers.index(col)
        except ValueError:
            raise KeyError(f"{col!r} is not a valid column header")
        return [self._get_cell(r, col_idx) for r in self._iter_slice(rows, 0)]

    def _set_column(self, col: TblKey, value: Iterable, rows: slice = slice(None)):
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

    def _del_column(self, col: TblKey) -> None:
        try:
            col_idx = self.column_headers.index(col)
        except ValueError:
            raise KeyError(f"{col!r} is not a valid column header")
        return self._widget._mgui_remove_column(col_idx)

    def _del_row(self, row: TblKey) -> None:
        try:
            row_idx = self.row_headers.index(row)
        except ValueError:
            raise KeyError(f"{row!r} is not a valid row header")
        self._del_rowi(row_idx)

    def _del_rowi(self, row: int) -> None:
        self._widget._mgui_remove_row(row)

    def _get_row(self, row: TblKey, cols: slice = slice(None)) -> list:
        """Get row by row header."""
        try:
            row_idx = self.row_headers.index(row)
        except ValueError:
            raise KeyError(f"{row!r} is not a valid row header")
        return self._get_rowi(row_idx, cols)

    def _get_rowi(self, row: int, cols: slice = slice(None)) -> list:
        """Get row by row index."""
        self._assert_row(row)
        return [self._get_cell(row, c) for c in self._iter_slice(cols, 1)]

    def _set_row(self, row: TblKey, value: list, cols: slice = slice(None)):
        """Set row by row header."""
        try:
            row_idx = self.row_headers.index(row)
        except ValueError:
            raise KeyError(f"{row!r} is not a valid row header")
        self._set_rowi(row_idx, value, cols)

    def _set_rowi(self, row: int, value: list, cols: slice = slice(None)):
        """Set row by row index."""
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

    # #### EXPORT METHODS #####

    def to_dataframe(self) -> "pd.DataFrame":
        """Convert TableData to dataframe."""
        try:
            import pandas

            return pandas.DataFrame(
                self.data.to_list(), self.row_headers, self.column_headers
            )
        except ImportError as e:
            raise ImportError(
                "Must install Pandas to convert to convert Table to DataFrame."
            ) from e

    # fmt: off
    @overload
    def to_dict(self, orient: Literal['dict']) -> Dict[TblKey, Dict[TblKey, list]]: ...  # noqa
    @overload
    def to_dict(self, orient: Literal['list']) -> Dict[TblKey, list]: ...  # noqa
    @overload
    def to_dict(self, orient: Literal['split']) -> Dict[TblKey, Collection]: ...  # noqa
    @overload
    def to_dict(self, orient: Literal['records']) -> List[Dict[TblKey, Any]]: ...  # noqa
    @overload
    def to_dict(self, orient: Literal['index']) -> Dict[TblKey, Dict[TblKey, list]]: ...  # noqa
    @overload
    def to_dict(self, orient: Literal['series']) -> Dict[TblKey, 'pd.Series']: ...  # noqa
    # fmt: on

    def to_dict(self, orient: str = "dict") -> Union[list, dict]:
        """Convert the Table to a dictionary.

        The type of the key-value pairs can be customized with the parameters
        (see below).

        Parameters
        ----------
        orient : str {'dict', 'list', 'series', 'split', 'records', 'index'}
            Determines the type of the values of the dictionary.

            - 'dict' (default) : dict like {column -> {index -> value}}
            - 'list' : dict like {column -> [values]}
            - 'split' : dict like
              {'index' -> [index], 'columns' -> [columns], 'data' -> [values]}
            - 'records' : list like
              [{column -> value}, ... , {column -> value}]
            - 'index' : dict like {index -> {column -> value}}
            - 'series' : dict like {column -> Series(values)}

        """
        orient = orient.lower()
        col_head = self.column_headers
        row_head = self.row_headers
        nrows, ncols = self.shape
        if _contains_duplicates(col_head):
            warn("Table column headers are not unique, some columns will be omitted.")
        if orient == "dict":
            if _contains_duplicates(row_head):
                warn("Table row headers are not unique, some rows will be omitted.")
            return {
                col_head[c]: {row_head[r]: self._get_cell(r, c) for r in range(nrows)}
                for c in range(ncols)
            }
        if orient == "list":
            return dict(self)
        if orient == "split":
            return {"data": self.data.to_list(), "index": row_head, "columns": col_head}
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

                return {header: Series(self[header]) for header in col_head}
            except ImportError as e:
                raise ImportError("Must install pandas to use to_dict('series')") from e

        raise ValueError(
            "'orient' argument to 'to_dict' must be one of "
            "('dict', list, 'split', 'records', 'index', 'series)"
        )


class DataView:
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
    # fmt: on

    def __getitem__(self, idx: Union[IndexKey, Tuple[IndexKey, IndexKey]]) -> Any:
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
                    return obj._get_rowi(r_idx, c_idx)
            elif isinstance(r_idx, slice):
                if isinstance(c_idx, int):
                    return obj._get_column(c_idx, r_idx)
                if isinstance(c_idx, slice):
                    return [obj._get_rowi(r, c_idx) for r in obj._iter_slice(r_idx, 0)]
        raise ValueError(f"Not a valid idx for __getitem__ {idx!r}")

    def __setitem__(
        self, idx: Union[IndexKey, Tuple[IndexKey, IndexKey]], value: Any
    ) -> None:
        """Set index."""
        # TODO: deal with bad shapes
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
                    return obj._set_rowi(r_idx, value, c_idx)
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
                        obj._set_rowi(r, v, c_idx)
                    return
        raise ValueError(f"Not a valid idx for __setitem__ {idx!r}")

    def __delitem__(self, idx: Union[IndexKey, Tuple[IndexKey, IndexKey]]):
        """Get index."""
        if isinstance(idx, (int, slice)):
            return self.__delitem__((idx, slice(None)))
        obj = self._obj
        if isinstance(idx, tuple):
            assert len(idx) == 2, "Table Widget only accepts 2 arguments to __delitem__"
            r_idx, c_idx = idx
            for i in idx:
                if not (isinstance(i, int) or i == slice(None)):
                    raise ValueError(f"Can only delete full rows/columns, not {idx!r}")
            if isinstance(r_idx, int):
                if c_idx == slice(None):
                    return obj._del_rowi(r_idx)
                raise ValueError("Can only delete full rows/columns, not cells")
            elif isinstance(r_idx, slice):
                if isinstance(c_idx, int):
                    return obj._del_column(obj.column_headers[c_idx])
                else:
                    for r in obj._iter_slice(r_idx, 0):
                        obj._del_rowi(r)
                    return
        raise ValueError(f"Not a valid idx for __getitem__ {idx!r}")

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


def _from_nested_column_dict(data: dict) -> Tuple[List[list], list]:
    """Return 2D data and row headers from a dict of nested dicts."""
    _index = {frozenset(i) for i in data.values()}
    if len(_index) > 1:
        try:
            import pandas as pd

            df = pd.DataFrame(data)
            return df.values, df.index
        except ImportError:
            raise ValueError(
                "All row-dicts must have the same keys. "
                "Install pandas for better table-from-dict support."
            )
    # preserve order of keys
    index = []
    for v in data.values():
        index = list(v)
        break

    new_data = []
    for col, s in data.items():
        new_data.append([s[i] for i in index])
    return list(list(x) for x in zip(*new_data)), index


def _from_dict(data: dict, dtype=None) -> Tuple[List[list], list, list]:
    """Return normalized data from dict of array-like or row-dicts.

    logic from pandas.DataFrame.from_dict
    """
    if set(data) == {"data", "index", "columns"}:
        return data["data"], data["index"], data["columns"]
    columns = list(data)
    if isinstance(list(data.values())[0], dict):
        _data, index = _from_nested_column_dict(data)
    else:
        _data = list(list(x) for x in zip(*data.values()))
        index = []
    return _data, index, columns


def _from_records(data: List[Dict[TblKey, Any]]) -> Tuple[List[list], list, list]:
    """Return normalized data from a list of column dicts."""
    if not data:
        return [], [], []
    _columns = {frozenset(i) for i in data}
    if len(_columns) > 1:
        try:
            import pandas as pd

            df = pd.DataFrame(data)
            return df.values, df.index, df.columns
        except ImportError:
            raise ValueError(
                "All column-dicts must have the same keys. "
                "Install pandas for better table-from-dict support."
            )
    columns = list(data[0])
    _data = [list(d.values()) for d in data]
    return _data, [], columns


def _validate_table_data(data, index, column):
    """Make sure data matches shape of index and column."""
    nr = len(data)
    if not nr:
        return
    try:
        nc = len(data[0])
    except (TypeError, IndexError):
        nc = 1
    if index is not None and len(index) and len(index) != nr:
        raise ValueError(
            f"Shape of passed values is ({nr}, {nc}), "
            f"headers imply ({len(index)}, {len(column)})"
        )
    if column is not None and len(column) and len(column) != nc:
        warn(
            f"Shape of passed values is ({nr}, {nc}), "
            f"headers imply ({len(index)}, {len(column)}). Data will be truncated."
        )
