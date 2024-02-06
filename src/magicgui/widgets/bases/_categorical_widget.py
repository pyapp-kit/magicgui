from __future__ import annotations

from enum import Enum, EnumMeta
from typing import TYPE_CHECKING, Any, Callable, cast

from magicgui.types import ChoicesType, Undefined, _Undefined

from ._value_widget import T, ValueWidget

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from magicgui.widgets import protocols

    from ._widget import WidgetKwargs


class CategoricalWidget(ValueWidget[T]):
    """Widget with a value and choices.  Wraps CategoricalWidgetProtocol.

    Parameters
    ----------
    value : Any, optional
        The initially selected choice.
    choices : Enum, Iterable, or Callable
        Available choices displayed in the combo box.
    bind : Callable[[ValueWidget], Any] | Any, optional
        A value or callback to bind this widget. If provided, whenever
        [`widget.value`][magicgui.widgets.bases.ValueWidget.value] is
        accessed, the value provided here will be returned instead. `bind` may be a
        callable, in which case `bind(self)` will be returned (i.e. your bound callback
        must accept a single parameter, which is this widget instance).
    nullable : bool, optional
        If `True`, the widget will accepts `None` as a valid value, by default `False`.
    **base_widget_kwargs : Any
        All additional keyword arguments are passed to the base
        [`magicgui.widgets.Widget`][magicgui.widgets.Widget] constructor.
    """

    _widget: protocols.CategoricalWidgetProtocol
    null_string: str = "-----"
    _allow_multiple = False

    def __init__(
        self,
        value: T | _Undefined = Undefined,
        choices: ChoicesType = (),
        *,
        allow_multiple: bool | None = None,
        bind: T | Callable[[ValueWidget], T] | _Undefined = Undefined,
        nullable: bool = False,
        **base_widget_kwargs: Unpack[WidgetKwargs],
    ) -> None:
        if allow_multiple is not None:
            self._allow_multiple = allow_multiple
        self._default_choices = choices
        super().__init__(
            value=value, bind=bind, nullable=nullable, **base_widget_kwargs
        )

    def _post_init(self) -> None:
        super()._post_init()
        self.reset_choices()
        self.native_parent_changed.connect(self.reset_choices)

    @property
    def value(self) -> T:
        """Return current value of the widget."""
        return ValueWidget.value.fget(self)  # type: ignore

    @value.setter
    def value(self, value: T) -> None:
        if isinstance(value, (list, tuple)) and self._allow_multiple:
            if any(v not in self.choices for v in value):
                raise ValueError(
                    f"{value!r} is not a valid choice. must be in {self.choices}"
                )
        elif value not in self.choices:
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

    def reset_choices(self, *_: Any) -> None:
        """Reset choices to the default state.

        If self._default_choices is a callable, this may NOT be the exact same set of
        choices as when the widget was instantiated, if the callable relies on external
        state.
        """
        self.choices = self._default_choices  # type: ignore

    @property
    def current_choice(self) -> str:
        """Return the text of the currently selected choice."""
        return self._widget._mgui_get_current_choice()

    def __len__(self) -> int:
        """Return the number of choices."""
        return self._widget._mgui_get_count()

    def get_choice(self, choice_name: str) -> T:
        """Get data for the provided ``choice_name``."""
        return cast(T, self._widget._mgui_get_choice(choice_name))

    def set_choice(self, choice_name: str, data: Any | None = None) -> None:
        """Set data for the provided ``choice_name``."""
        data = data if data is not None else choice_name
        self._widget._mgui_set_choice(choice_name, data)
        if choice_name == self.current_choice:
            self.changed.emit(self.value)

    def del_choice(self, choice_name: str) -> None:
        """Delete the provided ``choice_name`` and associated data."""
        self._widget._mgui_del_choice(choice_name)

    @property
    def choices(self) -> tuple[T | None, ...]:
        """Available value choices for this widget."""
        _choices = tuple(i[1] for i in self._widget._mgui_get_choices())
        if self._nullable and None not in _choices:
            return (*_choices, None)
        return _choices

    @choices.setter
    def choices(self, choices: ChoicesType) -> None:
        str_func: Callable = _get_name if isinstance(choices, EnumMeta) else str  # type: ignore
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
            # ensure that when setting choices with a callable,
            # the default choices are also updated with that callable
            self._default_choices = choices
        else:
            _choices = choices

        _normed: list[tuple[str, Any]] = list(_choices)
        if not all(isinstance(i, tuple) and len(i) == 2 for i in _normed):
            _normed = [(str_func(i), i) for i in _choices]
        if self._nullable:
            _normed.insert(0, (self.null_string, self.null_value))
        return self._widget._mgui_set_choices(_normed)


def _get_name(obj: Enum) -> str:
    return str(obj.name)
