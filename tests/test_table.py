"""Tests for the Table widget."""
import sys

import pytest

from magicgui.widgets import PushButton, Slider, Table

_TABLE_DATA = {
    # column-dict-of-lists
    "list": {"col_1": [1, 4], "col_2": [2, 5], "col_3": [3, 6]},
    # column-dict-of-row-dicts
    "dict": {
        "col_1": {"r1": 1, "r2": 4},
        "col_2": {"r1": 2, "r2": 5},
        "col_3": {"r1": 3, "r2": 6},
    },
    # list-of-lists
    "data": [[1, 2, 3], [4, 5, 6]],
    # Records: List-of-column-dict
    "records": [
        {"col_1": 1, "col_2": 2, "col_3": 3},
        {"col_1": 4, "col_2": 5, "col_3": 6},
    ],
    # 3-tuple of data, index, column
    "tuple": ([[1, 2, 3], [4, 5, 6]], ("r1", "r2"), ("c1", "c2", "c3")),
    # split-dict
    "split": {
        "data": [[1, 2, 3], [4, 5, 6]],
        "index": ("r1", "r2"),
        "columns": ("c1", "c2", "c3"),
    },
}


@pytest.mark.parametrize("key", _TABLE_DATA)
def test_table(key):
    """Test a few ways to input tables."""
    input = _TABLE_DATA[key]
    table = Table(value=input)
    if key == "split":
        assert table.value == input
    if key not in ("tuple", "data"):
        # make sure the output is the same as the input
        assert table.to_dict(key) == input
        # can also test equality of table widgets
        assert Table(value=table.to_dict(key)) == table
        table.row_headers = ("x", "x")
        table.column_headers = ("a", "a", "b")
        with pytest.warns(UserWarning):
            table.to_dict(key)


def test_constructor():
    """Test various combinations of data, index, column."""
    t = Table(index=["r"], columns=["a", "b"], name="My Table")
    assert t.shape == (1, 2)
    assert t.row_headers == ("r",)
    assert tuple(t) == ("a", "b")
    assert repr(t).split(" at")[0] == "Table(name='My Table', shape=(1, 2)"

    t = Table(index=["a", "b"], columns=["c"])
    assert t.shape == (2, 1)
    assert t.row_headers == ("a", "b")
    assert t.column_headers == ("c",)

    assert Table([1, 2]).shape == (2, 1)  # single list is interpreted as column
    assert Table([[1, 2]]).shape == (1, 2)  # nested lists are rows

    # aruments to constructor override those in a dict value
    t = Table(_TABLE_DATA["dict"], columns=("x", "y", "z"))
    assert t.column_headers == ("x", "y", "z")

    # data and headers can be provided seperately
    t = Table([[1, 2, 3], [4, 5, 6]], columns=["col_1", "col_2", "col_3"])
    assert dict(t) == _TABLE_DATA["list"]
    # or together
    assert t == Table(_TABLE_DATA["list"])

    with pytest.warns(UserWarning):
        # more columns than provided... truncated to provided columns
        assert Table([[1, 2]], index=["a"], columns=["v"]).shape == (1, 1)

    with pytest.raises(ValueError):
        # more rows than provided index, raises
        Table([[1], [2]], index=["a"], columns=["v"])
    with pytest.raises(ValueError):
        # same as above
        Table([1, 2], index=["a"], columns=["v"])


def test_adding_deleting_to_empty_table():
    """Test the dict-like api starting with empty table."""
    table = Table()
    assert not any(table.data.to_list())
    assert table.shape == (0, 0)
    # add a new column
    table["c1"] = [1, 2, 3, 4]
    assert table["c1"] == [1, 2, 3, 4]
    assert table.shape == (4, 1)
    # add one with more data
    table["c2"] = [1, 2, 3, 4, 5, 6]
    assert table.shape == (6, 2)
    # add one with less data
    table["c3"] = [1, 2, 3]
    assert table.shape == (6, 3)
    assert table.size == 18
    assert table["c3"][5] is None  # it fills to meet the rows

    assert table.row_headers == (0, 1, 2, 3, 4, 5)
    assert table._get_row(table.row_headers[0]) == [1, 1, 1]
    table._del_row(table.row_headers[0])
    assert table._get_row(table.row_headers[0]) == [2, 2, 2]

    # we can use dict methods
    table.update({"c1": [1, 1]})  # it will clear the extra...
    assert table["c1"] == [1, 1, None, None, None]

    # we can del
    del table["c2"]
    assert "c2" not in table
    with pytest.raises(KeyError):
        table["c2"]  # does not exist

    with pytest.raises(TypeError):
        # not a collection
        table["c5"] = 1  # type: ignore

    with pytest.raises(KeyError):
        del table["c219"]  # does not exist

    table.clear()
    assert table.shape == (0, 0)
    assert not table.column_headers
    assert not table.row_headers


def test_orient_index():
    """Test to_dict with orient = 'index' ."""
    table = Table(value=_TABLE_DATA["dict"])
    expected = {
        "r1": {"col_1": 1, "col_2": 2, "col_3": 3},
        "r2": {"col_1": 4, "col_2": 5, "col_3": 6},
    }
    assert table.to_dict("index") == expected

    table = Table(value=_TABLE_DATA["dict"])
    table.row_headers = ("a", "a")
    with pytest.warns(UserWarning):
        table.to_dict("index")

    with pytest.raises(ValueError):
        table.to_dict("notathing")  # type: ignore


def test_table_from_numpy():
    """Test inputting tables from numpy array."""
    np = pytest.importorskip("numpy")
    data = np.arange(12).reshape(4, 3)

    table = Table(value=data)
    assert np.allclose(table.data.to_numpy(), data)


INDICES = (
    1,
    (2, 2),
    (slice(None), 2),
    (slice(None), slice(None)),
    (slice(1, 3), slice(3)),
    (slice(1, None, 3), slice(None, 3)),
    slice(None, None, 2),
    (slice(None), slice(None, None, 2)),
)
VALUES = (
    (7,) * 4,
    6,
    (7,) * 6,
    [[1] * 4] * 6,
    [[1] * 3] * 2,
    [[1] * 3] * 2,
    [[1] * 4] * 3,
    [[1] * 2] * 6,
)


@pytest.mark.parametrize("index", INDICES)
def test_dataview_getitem(index):
    """Test that table.data can be indexed like a numpy array."""
    np = pytest.importorskip("numpy")
    data = np.arange(24).reshape(6, 4)

    table = Table(value=data)
    assert np.allclose(table.data[index], data[index])


@pytest.mark.parametrize("index, value", zip(INDICES, VALUES))
def test_dataview_setitem(index, value):
    """Test that table.data can be indexed like a numpy array."""
    np = pytest.importorskip("numpy")
    data = np.arange(24).reshape(6, 4)

    table = Table(value=data)
    table.data[index] = value
    assert not np.allclose(table.data.to_list(), data)
    data[index] = value
    assert np.allclose(table.data.to_list(), data)


def test_dataview_delitem():
    """Test that table.data can be indexed like a numpy array."""
    input = _TABLE_DATA["dict"]
    table = Table(value=input)
    row_keys = table.keys("row")  # also demoing keys views
    col_keys = table.keys("column")  # also demoing keys views
    assert list(row_keys) == ["r1", "r2"]
    assert list(col_keys) == ["col_1", "col_2", "col_3"]
    del table.data[1]
    assert not table.to_dict("dict") == input
    assert list(row_keys) == ["r1"]
    assert list(col_keys) == ["col_1", "col_2", "col_3"]
    del table.data[:, 2]
    assert list(row_keys) == ["r1"]
    assert list(col_keys) == ["col_1", "col_2"]

    with pytest.raises(ValueError):
        del table.data[0, 0]  # cannot delete cells


def test_dataview_repr():
    """Test the repr for table.data."""
    table = Table(_TABLE_DATA["dict"], name="My Table")
    assert (
        repr(table.data).split(" at")[0]
        == "<Data for Table(name='My Table', shape=(2, 3)"
    )


def test_table_from_pandas():
    """Test inputting tables from pandas dataframe."""
    pd = pytest.importorskip("pandas", reason="Pandas required for some tables tests")
    df = pd.DataFrame.from_dict(_TABLE_DATA["dict"])
    table = Table(value=df)
    table.to_dataframe() == df


def test_orient_series():
    """Test to_dict with orient = 'index' ."""
    pd = pytest.importorskip("pandas", reason="Pandas required for some tables tests")
    table = Table(value=_TABLE_DATA["dict"])
    out = table.to_dict("series")
    assert all(isinstance(s, pd.Series) for s in out.values())


ugly_dict = {
    "col1": {"r1": 8, "r2": 9},
    "col2": {"r1": 10, "r3": 11},
    "col3": {"r7": 12, "r9": 12},
}
ugly_records = [{"col1": 1, "col2": 2}, {"col1": 3}, {"col3": 4, "col2": 5}]


def test_joins_with_pandas():
    """Test that pandas can help with ugly data."""
    pd = pytest.importorskip("pandas", reason="Pandas required for some tables tests")

    t = Table(value=ugly_dict)
    assert t.shape == (5, 3)
    pd.testing.assert_frame_equal(t.to_dataframe(), pd.DataFrame(ugly_dict))

    t2 = Table(value=ugly_records)
    assert t2.shape == (3, 3)
    pd.testing.assert_frame_equal(t2.to_dataframe(), pd.DataFrame(ugly_records))


def test_joins_without_pandas(monkeypatch):
    """Test that we give a useful error with ugly data if pandas is not available."""
    monkeypatch.setitem(sys.modules, "pandas", None)
    with pytest.raises(ValueError) as e:
        Table(value=ugly_dict)
        assert "Install pandas" in str(e)

    with pytest.raises(ValueError) as e:
        Table(value=ugly_records)
        assert "Install pandas" in str(e)


def test_widget_in_table():
    """Test we can put widgets in the table!."""
    table = Table()
    button = PushButton(text="hi")
    slider = Slider(value=50)
    table["a"] = [button, 1, slider, "wow!"]
    assert table["a"] == [button, 1, slider, "wow!"]


def test_view_reprs():
    """Test our custom DictView objects."""
    table = Table(value=_TABLE_DATA["dict"])
    assert repr(table.keys()) == "column_headers(['col_1', 'col_2', 'col_3'])"
    assert repr(table.keys("column")) == "column_headers(['col_1', 'col_2', 'col_3'])"
    assert repr(table.keys("row")) == "row_headers(['r1', 'r2'])"
    assert repr(table.items()) == "table_items(3 columns)"
    assert repr(table.items("column")) == "table_items(3 columns)"
    assert repr(table.items("row")) == "table_items(2 rows)"


def test_row_access_errors():
    """Test various exceptions upon bad access."""
    table = Table(value=_TABLE_DATA["dict"])
    table._set_row("r1", [9, 9, 9])
    assert table._get_row("r1") == [9, 9, 9]
    with pytest.raises(KeyError):
        table._get_row("nonsense")
    with pytest.raises(KeyError):
        table._set_row("nonsense", [1, 2, 3])
    with pytest.raises(KeyError):
        table._del_row("nonsense")
    with pytest.raises(IndexError):
        table._get_rowi(10)

    assert table._assert_col(0) == 0
    with pytest.raises(IndexError):
        table._assert_col(10)


def test_check_new_headers():
    """Check that we get good error messages when setting bad headers."""
    table = Table(value=_TABLE_DATA["dict"])
    with pytest.raises(ValueError) as e:
        table.column_headers = ("a", "b", "c", "d")
        assert "Length mismatch" in str(e)
    with pytest.raises(ValueError) as e:
        table.row_headers = ("a", "b", "c", "d")
        assert "Length mismatch" in str(e)
