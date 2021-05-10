from enum import EnumMeta
from typing import Any, Callable, List, Tuple

from magicgui.types import ChoicesType
from magicgui.widgets import _protocols

from .value_widget import ValueWidget


class CategoricalWidget(ValueWidget):
    """Widget with a value and choices, Wraps CategoricalWidgetProtocol.

    Parameters
    ----------
    choices : Enum, Iterable, or Callable
        Available choices displayed in the combo box.
    """

    _widget: _protocols.CategoricalWidgetProtocol
    null_string: str = "-----"
    null_value = None

    def __init__(self, choices: ChoicesType = (), **kwargs):
        self._default_choices = choices
        super().__init__(**kwargs)

    def _post_init(self):
        super()._post_init()
        self.reset_choices()
        self.parent_changed.connect(self.reset_choices)

    @property
    def value(self):
        """Return current value of the widget."""
        return ValueWidget.value.fget(self)  # type: ignore

    @value.setter
    def value(self, value):
        if value not in self.choices:
            raise ValueError(
                f"{value!r} is not a valid choice. must be in {self.choices}"
            )
        return ValueWidget.value.fset(self, value)  # type: ignore

    @property
    def options(self) -> dict:
        """Return options currently being used in this widget."""
        d = super().options.copy()
        d.update({"choices": self._default_choices})
        return d

    def reset_choices(self, event=None):
        """Reset choices to the default state.

        If self._default_choices is a callable, this may NOT be the exact same set of
        choices as when the widget was instantiated, if the callable relies on external
        state.
        """
        self.choices = self._default_choices

    @property
    def current_choice(self) -> str:
        """Return the text of the currently selected choice."""
        return self._widget._mgui_get_current_choice()

    def __len__(self) -> int:
        """Return the number of choices."""
        return self._widget._mgui_get_count()

    def get_choice(self, choice_name: str):
        """Get data for the provided ``choice_name``."""
        self._widget._mgui_get_choice(choice_name)

    def set_choice(self, choice_name: str, data: Any = None):
        """Set data for the provided ``choice_name``."""
        data = data if data is not None else choice_name
        self._widget._mgui_set_choice(choice_name, data)
        if choice_name == self.current_choice:
            self.changed(value=self.value)

    def del_choice(self, choice_name: str):
        """Delete the provided ``choice_name`` and associated data."""
        self._widget._mgui_del_choice(choice_name)

    @property
    def choices(self):
        """Available value choices for this widget."""
        return tuple(i[1] for i in self._widget._mgui_get_choices())

    @choices.setter
    def choices(self, choices: ChoicesType):
        if isinstance(choices, EnumMeta):
            str_func: Callable = lambda x: str(x.name)
        else:
            str_func = str
        if isinstance(choices, dict):
            if "choices" not in choices or "key" not in choices:
                raise ValueError(
                    "When setting choices with a dict, the dict must have keys "
                    "'choices' (Iterable), and 'key' (callable that takes a each value "
                    "in `choices` and returns a string."
                )
            _choices = choices["choices"]
            str_func = choices["key"]
        elif not isinstance(choices, EnumMeta) and callable(choices):
            _choices = choices(self)

        else:
            _choices = choices

        _normed: List[Tuple[str, Any]] = list(_choices)
        if not all(isinstance(i, tuple) and len(i) == 2 for i in _normed):
            _normed = [(str_func(i), i) for i in _choices]
        if self._nullable:
            _normed.insert(0, (self.null_string, self.null_value))
        return self._widget._mgui_set_choices(_normed)
