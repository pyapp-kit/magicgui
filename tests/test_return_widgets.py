#!/usr/bin/env python

"""Tests return widget types"""

import pathlib
from datetime import date, datetime, time
from inspect import signature

import numpy as np
import pytest

import magicgui
from magicgui import widgets


def _dataframe_equals(object1, object2):
    assert object1.equals(object2)


def _ndarray_equals(object1: np.ndarray, object2: np.ndarray):
    assert np.array_equal(object1, object2)


def _default_equals(object1, object2):
    assert object1 == object2


def _generate_pandas_test_data():
    pd = pytest.importorskip(
        "pandas", reason="Pandas required for a return widget test"
    )
    return pd.DataFrame({"Res1": [1, 2, 3], "Res2": [4, 5, 6]})


parameterizations = [
    # pandas dataframe
    (
        _generate_pandas_test_data(),
        widgets.Table,
        _dataframe_equals,
    ),
    # numpy array
    (
        np.array([1, 1, 1, 2, 2, 2, 3, 3, 3]).reshape((3, 3)),
        widgets.Table,
        _ndarray_equals,
    ),
    # NOTE: disabling for now... these types are too broad to choose a table
    # # dict
    # ({"a": [1], "b": [2], "c": [3]}, widgets.Table, _default_equals),
    # # list
    # ([1, 2, 3], widgets.Table, _default_equals),
    # # tuple
    # (([[1], [2], [3]], ["A", "B", "C"], ["Row 1"]), widgets.Table, _default_equals),
    # boolean
    (True, widgets.LineEdit, _default_equals),
    # int
    (5, widgets.LineEdit, _default_equals),
    # float
    (3.5, widgets.LineEdit, _default_equals),
    # string
    ("foo", widgets.LineEdit, _default_equals),
    # path
    (pathlib.Path().absolute(), widgets.LineEdit, _default_equals),
    # date
    (date.today(), widgets.LineEdit, _default_equals),
    # time
    (time(), widgets.LineEdit, _default_equals),
    # datetime
    (datetime.now(), widgets.LineEdit, _default_equals),
    # range
    (range(10), widgets.LineEdit, _default_equals),
    # slice
    (slice(6), widgets.LineEdit, _default_equals),
]


def generate_magicgui(data):
    def func():
        return data

    sig = signature(func)
    func.__signature__ = sig.replace(return_annotation=type(data))

    return magicgui.magicgui(func, result_widget=True)


@pytest.mark.parametrize("data, expected_type, equality_check", parameterizations)
def test_return_widget_for_type(data, expected_type, equality_check):
    widget = generate_magicgui(data)
    equality_check(widget(), data)
    assert isinstance(widget._result_widget, expected_type)


def test_table_return_annotation():
    @magicgui.magicgui(result_widget=True)
    def f() -> "magicgui.widgets.Table":
        ...

    @magicgui.magicgui(result_widget=True)
    def f2() -> widgets.Table:
        ...

    assert isinstance(f._result_widget, widgets.Table)
    assert isinstance(f2._result_widget, widgets.Table)
