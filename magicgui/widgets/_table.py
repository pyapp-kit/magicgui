from ._bases import ValueWidget
from ._concrete import backend_widget

try:
    import pandas as pd
except ImportError as exc:

    class Table:
        """Table Widget REQUIRES PANDAS TO BE INSTALLED."""

        _exc = exc

        def __new__(cls, *args, **kwargs):
            """Raise ImportError, missing pandas."""
            raise ImportError(
                "Please install pandas to use tables in magicgui."
            ) from cls._exc


else:

    def _from_dataframe(df: pd.DataFrame):
        return df.values, df.index, df.columns

    def _from_dict(data, orient="columns"):
        """Construct _MguiTable from dict of array-like or dicts."""
        df = pd.DataFrame.from_dict(data, orient=orient)
        return _from_dataframe(df)

    @backend_widget
    class Table(ValueWidget):  # type: ignore
        """A table widget for pandas, numpy, or dict-of-list data."""

        @property
        def value(self):
            """Return current value of the widget."""
            values, index, columns = self._widget._mgui_get_value()
            return pd.DataFrame(values, index=index, columns=columns)

        @value.setter
        def value(self, value):
            if isinstance(value, dict):
                self._widget._mgui_set_value(_from_dict(value))
            elif isinstance(value, pd.DataFrame):
                self._widget._mgui_set_value(_from_dataframe(value))
            elif hasattr(value, "__array_interface__"):
                self._widget._mgui_set_value((value, [], []))
            else:
                raise TypeError("Table value must be a dict, dataframe, or array")

        def __repr__(self) -> str:
            """Return string repr."""
            return "Table(name={self.name})\n" + repr(self.value)
