import pytest

from magicgui.widgets import Table

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
    table: Table = Table(value=input)
    if key not in ("tuple", "data"):
        # make sure the output is the same as the input
        assert table.to_dict(key) == input
        # can also test equality of table widgets
        assert Table(value=table.to_dict(key)) == table


def test_table_from_numpy():
    """Test inputting tables from numpy array."""
    np = pytest.importorskip("numpy")
    data = np.arange(12).reshape(4, 3)

    table: Table = Table(value=data)
    assert np.allclose(table.data.to_numpy(), data)


INDICES = (
    1,
    (slice(None), 2),
    (slice(None), slice(None)),
    (slice(1, 3), slice(3)),
    (slice(1, None, 3), slice(None, 3)),
    slice(None, None, 2),
    (slice(None), slice(None, None, 2)),
)


@pytest.mark.parametrize("index", INDICES)
def test_dataview_from_numpy(index):
    """Test that table.data can be indexed like a numpy array."""
    np = pytest.importorskip("numpy")
    data = np.arange(24).reshape(6, 4)

    table: Table = Table(value=data)
    assert np.allclose(table.data[index], data[index])


def test_table_from_pandas():
    """Test inputting tables from pandas dataframe."""
    pd = pytest.importorskip("pandas", reason="Install pandas to test tables")
    df = pd.DataFrame.from_dict(_TABLE_DATA["dict"])
    table: Table = Table(value=df)
    table.to_dataframe() == df
