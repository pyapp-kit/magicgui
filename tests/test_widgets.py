import pytest

from magicgui import magicgui, widgets
from magicgui.widgets._table import _value_to_table_data


@pytest.mark.parametrize(
    "WidgetClass", [getattr(widgets, n) for n in widgets.__all__ if n != "Widget"]
)
def test_widgets(WidgetClass):
    """Test that we can retrieve getters, setters, and signals for most Widgets."""
    _ = WidgetClass()


def test_autocall_no_runtime_error():
    """Make sure changing a value doesn't cause an autocall infinite loop."""

    @magicgui(auto_call=True, result_widget=True)
    def func(input=1):
        return round(input, 4)

    func.input.value = 2


def test_delete_widget():
    """We can delete widgets from containers."""
    a = widgets.Label(name="a")
    container = widgets.Container(widgets=[a])
    # we can delete widgets
    del container.a
    with pytest.raises(AttributeError):
        getattr(container, "a")

    # they disappear from the layout
    with pytest.raises(ValueError):
        container.index(a)


dict_of_dicts = {
    "col_1": {"r1": 3, "r2": 2, "r3": 1, "r4": 0},
    "col_2": {"r2": "b", "r4": "d", "r3": "c", "r1": "a"},
}
list_of_lists = [[8, 1, 4], [3, 7, 4]]
_TABLE_DATA = [
    {"col_1": [3, 2, 1, 0], "col_2": ["a", "b", "c", "d"]},
    dict_of_dicts,
    list_of_lists,
    (list_of_lists, ("r1", "r2"), ("c1", "c2", "c3")),
]


@pytest.mark.parametrize("data", _TABLE_DATA)
def test_table(data):
    """Test a few ways to input tables."""
    table = widgets.Table(value=data)
    assert [tuple(i) for i in table.value[0]] == [
        tuple(i) for i in _value_to_table_data(data)[0]
    ]


def test_table_from_numpy():
    """Test inputting tables from numpy array."""
    np = pytest.importorskip("numpy")
    data = np.random.randint(0, 10, (4, 3))
    table = widgets.Table(value=data)
    assert [tuple(i) for i in table.value[0]] == [
        tuple(i) for i in _value_to_table_data(data)[0]
    ]


def test_table_from_pandas():
    """Test inputting tables from pandas dataframe."""
    pd = pytest.importorskip("pandas", reason="Install pandas to test tables")
    data = pd.DataFrame.from_dict(dict_of_dicts)
    table = widgets.Table(value=data)
    assert [tuple(i) for i in table.value[0]] == [
        tuple(i) for i in _value_to_table_data(data)[0]
    ]
