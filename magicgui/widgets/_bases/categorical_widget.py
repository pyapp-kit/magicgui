import inspect
import warnings
from enum import EnumMeta
from typing import Any, Callable

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

    def del_choice(self, choice_name: str, data: Any = None):
        """Delete the provided ``choice_name`` and associated data."""
        data = data if data is not None else choice_name

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
            if not ("choices" in choices and "key" in choices):
                raise ValueError(
                    "When setting choices with a dict, the dict must have keys "
                    "'choices' (Iterable), and 'key' (callable that takes a each value "
                    "in `choices` and returns a string."
                )
            _choices = choices["choices"]
            str_func = choices["key"]
        elif not isinstance(choices, EnumMeta) and callable(choices):
            try:
                _choices = choices(self)
            except TypeError:

                n_params = len(inspect.signature(choices).parameters)
                if n_params > 1:
                    warnings.warn(
                        "\n\nAs of magicgui 0.2.0, when providing a callable to "
                        "`choices`, the\ncallable may accept only a single positional "
                        "argument (which will\nbe an instance of "
                        "`magicgui.widgets._bases.CategoricalWidget`),\nand must "
                        "return an iterable (the choices to show).\nFunction "
                        f"'{choices.__module__}.{choices.__name__}' accepts {n_params} "
                        "arguments.\nIn the future, this will raise an exception.\n",
                        FutureWarning,
                    )
                    # pre 0.2.0 API
                    _choices = choices(self.native, self.annotation)  # type: ignore
                else:
                    raise
        else:
            _choices = choices
        if not all(isinstance(i, tuple) and len(i) == 2 for i in _choices):
            _choices = [(str_func(i), i) for i in _choices]
        return self._widget._mgui_set_choices(_choices)
