"""Widgets backed by a backend implementation, ready to be instantiated by the user.

All of these widgets should provide the `widget_type` argument to their
super().__init__ calls.
"""
from __future__ import annotations

import inspect
import math
import os
import sys
from pathlib import Path
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Sequence,
    Tuple,
    TypeVar,
    overload,
)
from weakref import ref

from docstring_parser import DocstringParam, parse
from typing_extensions import Literal, get_args, get_origin

from magicgui.application import use_app
from magicgui.types import FileDialogMode, PathLike, WidgetOptions
from magicgui.widgets import _protocols
from magicgui.widgets._bases.container_widget import DialogWidget
from magicgui.widgets._bases.mixins import _OrientationMixin, _ReadOnlyMixin

from ._bases import (
    ButtonWidget,
    CategoricalWidget,
    ContainerWidget,
    MainWindowWidget,
    MultiValuedSliderWidget,
    RangedWidget,
    SliderWidget,
    TransformedRangedWidget,
    ValueWidget,
    Widget,
    create_widget,
)
from ._bases.value_widget import UNSET, _Unset

BUILDING_DOCS = sys.argv[-2:] == ["build", "docs"]


def _param_list_to_str(param_list: list[DocstringParam]) -> str:
    """Format Parameters section for numpy docstring from list of tuples."""
    out = []
    out += ["Parameters", len("Parameters") * "-"]
    for param in param_list:
        parts = []
        if param.arg_name:
            parts.append(param.arg_name)
        if param.type_name:
            parts.append(param.type_name)
        if not parts:
            continue
        out += [" : ".join(parts)]
        if param.description and param.description.strip():
            out += [" " * 4 + line for line in param.description.split("\n")]
    out += [""]
    return "\n".join(out)


def merge_super_sigs(cls, exclude=("widget_type", "kwargs", "args", "kwds", "extra")):
    """Merge the signature and kwarg docs from all superclasses, for clearer docs.

    Parameters
    ----------
    cls : Type
        The class being modified
    exclude : tuple, optional
        A list of parameter names to excluded from the merged docs/signature,
        by default ("widget_type", "kwargs", "args", "kwds")

    Returns
    -------
    cls : Type
        The modified class (can be used as a decorator)
    """
    params = {}
    param_docs: list[DocstringParam] = []
    for sup in reversed(inspect.getmro(cls)):
        try:
            sig = inspect.signature(getattr(sup, "__init__"))
        # in some environments `object` or `abc.ABC` will raise ValueError here
        except ValueError:
            continue
        for name, param in sig.parameters.items():
            if name in exclude:
                continue
            params[name] = param

        param_docs += parse(getattr(sup, "__doc__", "")).params

    # sphinx_autodoc_typehints isn't removing the type annotations from the signature
    # so we do it manually when building documentation.
    if BUILDING_DOCS:
        params = {
            k: v.replace(annotation=inspect.Parameter.empty) for k, v in params.items()
        }

    cls.__init__.__signature__ = inspect.Signature(
        sorted(params.values(), key=lambda x: x.kind)
    )
    param_docs = [p for p in param_docs if p.arg_name not in exclude]
    cls.__doc__ = (cls.__doc__ or "").split("Parameters")[0].rstrip() + "\n\n"
    cls.__doc__ += _param_list_to_str(param_docs)
    # this makes docs linking work... but requires that all of these be in __init__
    cls.__module__ = "magicgui.widgets"
    return cls


C = TypeVar("C")


@overload
def backend_widget(  # noqa
    cls: type[C],
    widget_name: str = None,
    transform: Callable[[type], type] = None,
) -> type[C]:
    ...


@overload
def backend_widget(  # noqa
    cls: Literal[None] = None,
    widget_name: str = None,
    transform: Callable[[type], type] = None,
) -> Callable[..., type[C]]:
    ...


def backend_widget(
    cls: type[C] = None,
    widget_name: str = None,
    transform: Callable[[type], type] = None,
) -> Callable | type[C]:
    """Decorate cls to inject the backend widget of the same name.

    The purpose of this decorator is to "inject" the appropriate backend
    `widget_type` argument into the `Widget.__init__` function, according to the
    app currently being used (i.e. returned by `use_app()`).

    Parameters
    ----------
    cls : Type, optional
        The class being decorated, by default None.
    widget_name : str, optional
        The name of the backend widget to wrap. If None, the name of the class being
        decorated is used.  By default None.
    transform : callable, optional
        A optional function that takes a class and returns a class.  May be used
        to transform the characteristics/methods of the class, by default None

    Returns
    -------
    cls : Type
        The final concrete class backed by a backend widget.
    """

    def wrapper(cls) -> type[Widget]:
        def __init__(self, **kwargs):
            app = use_app()
            assert app.native
            widget = app.get_obj(widget_name or cls.__name__)
            if transform:
                widget = transform(widget)
            kwargs["widget_type"] = widget
            super(cls, self).__init__(**kwargs)

        cls.__init__ = __init__
        cls = merge_super_sigs(cls)
        return cls

    return wrapper(cls) if cls else wrapper


@backend_widget
class EmptyWidget(ValueWidget):
    """A base widget with no value.

    This widget is primarily here to serve as a "hidden widget" to which a value or
    callback can be bound.
    """

    _hidden_value = inspect.Parameter.empty

    def get_value(self):
        """Return value if one has been manually set... otherwise return Param.empty."""
        return self._hidden_value

    @property
    def value(self):
        """Look for a bound value, otherwise fallback to `get_value`."""
        return super().value

    @value.setter
    def value(self, value):
        self._hidden_value = value

    def __repr__(self):
        """Return string repr (avoid looking for value)."""
        try:
            name = f"(name={self.name!r})" if self.name else ""
            return f"<{self.widget_type} {name}>"
        except AttributeError:  # pragma: no cover
            return f"<Uninitialized {self.widget_type}>"


@backend_widget
class Label(ValueWidget):
    """A non-editable text display."""


@backend_widget
class LineEdit(ValueWidget):
    """A one-line text editor."""


@backend_widget
class LiteralEvalLineEdit(ValueWidget):
    """A one-line text editor that evaluates strings as python literals."""


@backend_widget
class TextEdit(ValueWidget, _ReadOnlyMixin):  # type: ignore
    """A widget to edit and display both plain and rich text."""


@backend_widget
class DateTimeEdit(ValueWidget):
    """A widget for editing dates and times."""


@backend_widget
class DateEdit(ValueWidget):
    """A widget for editing dates."""


@backend_widget
class TimeEdit(ValueWidget):
    """A widget for editing times."""


@backend_widget
class PushButton(ButtonWidget):
    """A clickable command button."""


@backend_widget
class CheckBox(ButtonWidget):
    """A checkbox with a text label."""


@backend_widget
class RadioButton(ButtonWidget):
    """A radio button with a text label."""


@backend_widget
class SpinBox(RangedWidget):
    """A widget to edit an integer with clickable up/down arrows."""


@backend_widget
class FloatSpinBox(RangedWidget):
    """A widget to edit a float with clickable up/down arrows."""


@backend_widget
class ProgressBar(SliderWidget):
    """A progress bar widget."""

    def increment(self, val=None):
        """Increase current value by step size, or provided value."""
        self.value = self.get_value() + (val if val is not None else self.step)

    def decrement(self, val=None):
        """Decrease current value by step size, or provided value."""
        self.value = self.get_value() - (val if val is not None else self.step)

    # overriding because at least some backends don't have a step value for ProgressBar
    @property
    def step(self) -> float:
        """Step size for widget values."""
        return self._step

    @step.setter
    def step(self, value: float):
        self._step = value


@backend_widget
class Slider(SliderWidget):
    """A slider widget to adjust an integer value within a range."""


@backend_widget
class FloatSlider(SliderWidget):
    """A slider widget to adjust an integer value within a range."""


@backend_widget
class RangeSlider(MultiValuedSliderWidget):
    """A slider widget to adjust a range between two integer values within a range."""


@backend_widget
class FloatRangeSlider(MultiValuedSliderWidget):
    """A slider widget to adjust a range defined by two float values within a range."""


@merge_super_sigs
class LogSlider(TransformedRangedWidget):
    """A slider widget to adjust a numerical value logarithmically within a range.

    Parameters
    ----------
    base : Enum, Iterable, or Callable
        The base to use for the log, by default math.e.
    """

    _widget: _protocols.SliderWidgetProtocol

    def __init__(
        self,
        min: float = 1,
        max: float = 100,
        base: float = math.e,
        tracking=True,
        **kwargs,
    ):
        for key in ("maximum", "minimum"):
            if key in kwargs:
                import warnings

                warnings.warn(
                    f"The {key!r} keyword arguments has been changed to {key[:3]!r}. "
                    "In the future this will raise an exception\n",
                    FutureWarning,
                    stacklevel=2,
                )
                if key == "maximum":
                    max = kwargs.pop(key)
                else:
                    min = kwargs.pop(key)
        self._base = base
        app = use_app()
        assert app.native
        super().__init__(
            min=min,
            max=max,
            widget_type=app.get_obj("Slider"),
            **kwargs,
        )
        self.tracking = tracking

    @property
    def tracking(self) -> bool:
        """Return whether slider tracking is enabled.

        If tracking is enabled (the default), the slider emits the changed()
        signal while the slider is being dragged. If tracking is disabled,
        the slider emits the changed() signal only when the user releases
        the slider.
        """
        return self._widget._mgui_get_tracking()

    @tracking.setter
    def tracking(self, value: bool) -> None:
        """Set whether slider tracking is enabled."""
        self._widget._mgui_set_tracking(value)

    @property
    def _scale(self):
        minv = math.log(self.min, self.base)
        maxv = math.log(self.max, self.base)
        return (maxv - minv) / (self._max_pos - self._min_pos)

    def _value_from_position(self, position):
        minv = math.log(self.min, self.base)
        return math.pow(self.base, minv + self._scale * (position - self._min_pos))

    def _position_from_value(self, value):
        minv = math.log(self.min, self.base)
        pos = (math.log(value, self.base) - minv) / self._scale + self._min_pos
        return int(pos)

    @property
    def base(self):
        """Return base used for the log."""
        return self._base

    @base.setter
    def base(self, base):
        prev = self.value
        self._base = base
        self.value = prev


@backend_widget
class ComboBox(CategoricalWidget):
    """A dropdown menu, allowing selection between multiple choices."""


@backend_widget
class Select(CategoricalWidget):
    """A list of options, allowing selection between multiple choices."""

    _allow_multiple = True


@merge_super_sigs
class RadioButtons(CategoricalWidget, _OrientationMixin):  # type: ignore
    """An exclusive group of radio buttons, providing a choice from multiple choices."""

    def __init__(self, choices=(), orientation="vertical", **kwargs):
        app = use_app()
        assert app.native
        kwargs["widget_type"] = app.get_obj("RadioButtons")
        super().__init__(choices=choices, **kwargs)
        self.orientation = orientation


@backend_widget
class Container(ContainerWidget):
    """A Widget to contain other widgets."""


@backend_widget
class Dialog(DialogWidget):
    """A modal container."""


@backend_widget
class MainWindow(MainWindowWidget):
    """A Widget to contain other widgets."""


@merge_super_sigs
class FileEdit(Container):
    """A LineEdit widget with a button that opens a FileDialog.

    Parameters
    ----------
    mode : FileDialogMode or str
        - ``'r'`` returns one existing file.
        - ``'rm'`` return one or more existing files.
        - ``'w'`` return one file name that does not have to exist.
        - ``'d'`` returns one existing directory.
    filter : str, optional
        The filter is used to specify the kind of files that should be shown.
        It should be a glob-style string, like ``'*.png'`` (this may be
        backend-specific)
    """

    def __init__(
        self,
        mode: FileDialogMode = FileDialogMode.EXISTING_FILE,
        filter=None,
        nullable=False,
        **kwargs,
    ):
        value = kwargs.pop("value", None)
        if value is None:
            value = ""
        self.line_edit = LineEdit(value=value)
        self.choose_btn = PushButton()
        self.mode = mode  # sets the button text too
        self.filter = filter
        self._nullable = nullable
        kwargs["widgets"] = [self.line_edit, self.choose_btn]
        kwargs["labels"] = False
        kwargs["layout"] = "horizontal"
        super().__init__(**kwargs)
        self.margins = (0, 0, 0, 0)
        self._show_file_dialog = use_app().get_obj("show_file_dialog")
        self.choose_btn.changed.disconnect()
        self.line_edit.changed.disconnect()
        self.choose_btn.changed.connect(self._on_choose_clicked)
        self.line_edit.changed.connect(lambda: self.changed.emit(self.value))

    @property
    def mode(self) -> FileDialogMode:
        """Mode for the FileDialog."""
        return self._mode

    @mode.setter
    def mode(self, value: FileDialogMode | str):
        self._mode = FileDialogMode(value)
        self.choose_btn.text = self._btn_text

    @property
    def _btn_text(self) -> str:
        if self.mode is FileDialogMode.EXISTING_DIRECTORY:
            return "Choose directory"
        else:
            return "Select file" + ("s" if self.mode.name.endswith("S") else "")

    def _on_choose_clicked(self):
        _p = self.value
        if _p:
            start_path: Path = _p[0] if isinstance(_p, tuple) else _p
            _start_path: str | None = os.fspath(start_path.expanduser().absolute())
        else:
            _start_path = None
        result = self._show_file_dialog(
            self.mode,
            caption=self._btn_text,
            start_path=_start_path,
            filter=self.filter,
        )
        if result:
            self.value = result

    @property
    def value(self) -> tuple[Path, ...] | Path | None:
        """Return current value of the widget.  This may be interpreted by backends."""
        text = self.line_edit.value
        if self._nullable and not text:
            return None
        if self.mode is FileDialogMode.EXISTING_FILES:
            return tuple(Path(p) for p in text.split(", ") if p.strip())
        return Path(text)

    @value.setter
    def value(self, value: Sequence[PathLike] | PathLike | None):
        """Set current file path."""
        if value is None and self._nullable:
            value = ""
        elif isinstance(value, (list, tuple)):
            value = ", ".join(os.fspath(Path(p).expanduser().absolute()) for p in value)
        elif isinstance(value, (str, Path)):
            value = os.fspath(Path(value).expanduser().absolute())
        else:
            raise TypeError(
                f"value must be a string, or list/tuple of strings, got {type(value)}"
            )
        self.line_edit.value = value

    def __repr__(self) -> str:
        """Return string representation."""
        return f"FileEdit(mode={self.mode.value!r}, value={self.value!r})"


@merge_super_sigs
class RangeEdit(Container):
    """A widget to represent a python range object, with start/stop/step.

    A range object produces a sequence of integers from start (inclusive)
    to stop (exclusive) by step.  range(i, j) produces i, i+1, i+2, ..., j-1.
    start defaults to 0, and stop is omitted!  range(4) produces 0, 1, 2, 3.
    These are exactly the valid indices for a list of 4 elements.
    When step is given, it specifies the increment (or decrement).

    Parameters
    ----------
    start : int, optional
        The range start value, by default 0
    stop : int, optional
        The range stop value, by default 10
    step : int, optional
        The range step value, by default 1
    """

    def __init__(
        self,
        start: int = 0,
        stop: int = 10,
        step: int = 1,
        min: int | tuple[int, int, int] | None = None,
        max: int | tuple[int, int, int] | None = None,
        **kwargs,
    ):
        value = kwargs.pop("value", None)
        if value is not None and value is not UNSET:
            if not all(hasattr(value, x) for x in ("start", "stop", "step")):
                raise TypeError(f"Invalid value type for {type(self)}: {type(value)}")
            start, stop, step = value.start, value.stop, value.step
        minstart, minstop, minstep = self._validate_min_max(min, "min", -9999999)
        maxstart, maxstop, maxstep = self._validate_min_max(max, "max", 9999999)
        self.start = SpinBox(value=start, min=minstart, max=maxstart, name="start")
        self.stop = SpinBox(value=stop, min=minstop, max=maxstop, name="stop")
        self.step = SpinBox(value=step, min=minstep, max=maxstep, name="step")
        kwargs["widgets"] = [self.start, self.stop, self.step]
        kwargs.setdefault("layout", "horizontal")
        kwargs.setdefault("labels", True)
        kwargs.pop("nullable", None)
        super().__init__(**kwargs)

    @classmethod
    def _validate_min_max(cls, arg, name, default):
        """Validate input to the min/max arguments."""
        if isinstance(arg, (int, float)):
            return (int(arg),) * 3
        elif isinstance(arg, (list, tuple)):
            if len(arg) != 3:
                raise ValueError(f"{name} sequence must be length 3")
            return tuple(int(x) for x in arg)
        elif arg is not None:
            raise TypeError("min must be an integer or a 3-tuple of integers")
        else:
            return (int(default),) * 3

    @property
    def value(self) -> range:
        """Return current value of the widget.  This may be interpreted by backends."""
        return range(self.start.value, self.stop.value, self.step.value)

    @value.setter
    def value(self, value: range):
        """Set current file path."""
        self.start.value = value.start
        self.stop.value = value.stop
        self.step.value = value.step

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<{self.__class__.__name__} value={self.value!r}>"


class SliceEdit(RangeEdit):
    """A widget to represent `slice` objects, with start/stop/step.

    slice(stop)
    slice(start, stop[, step])

    Slice objects may be used for extended slicing (e.g. a[0:10:2])
    """

    @property  # type: ignore
    def value(self) -> slice:
        """Return current value of the widget.  This may be interpreted by backends."""
        return slice(self.start.value, self.stop.value, self.step.value)

    @value.setter
    def value(self, value: slice):
        """Set current file path."""
        self.start.value = value.start
        self.stop.value = value.stop
        self.step.value = value.step


_V = TypeVar("_V")


@merge_super_sigs
class ListEdit(Container):
    """A widget to represent a list of values.

    A ListEdit container can create a list with multiple objects of same type. It
    will contain many child widgets and their value is represented as a Python list
    object. If a list is given as the initial value, types of child widgets are
    determined from the contents. Number of contents can be adjusted with +/-
    buttons.

    Parameters
    ----------
    options: WidgetOptions, optional
        Widget options of child widgets.
    """

    def __init__(
        self,
        value: Iterable[_V] | _Unset = UNSET,
        layout: str = "horizontal",
        nullable: bool = False,
        options: WidgetOptions = None,
        **kwargs,
    ):
        self._args_type: type | None = None
        self._nullable = nullable
        super().__init__(layout=layout, labels=False, **kwargs)
        self.margins = (0, 0, 0, 0)

        if not isinstance(value, _Unset):
            # check type consistency
            types = {type(a) for a in value}
            if len(types) <= 1:
                if self._args_type is None:
                    self._args_type = types.pop()
            else:
                raise TypeError("values have inconsistent types.")
            _value: Iterable[_V] = value
        else:
            _value = []

        self._child_options = options or {}

        button_plus = PushButton(text="+", name="plus")
        button_plus.changed.connect(lambda: self._append_value())

        button_minus = PushButton(text="-", name="minus")
        button_minus.changed.connect(self._pop_value)

        if layout == "horizontal":
            button_plus.max_width = 40
            button_minus.max_width = 40

        self.append(button_plus)
        self.append(button_minus)

        for a in _value:
            self._append_value(a)

        self.btn_plus = button_plus
        self.btn_minus = button_minus

    @property
    def annotation(self):
        """Return type annotation for the parameter represented by the widget.

        ForwardRefs will be resolve when setting the annotation. For ListEdit,
        annotation will be like 'list[str]'.
        """
        return self._annotation

    @annotation.setter
    def annotation(self, value):
        if value is None:
            self._annotation = None
            self._args_type = None
            return

        from .._type_wrapper import resolve_annotation

        value = resolve_annotation(value)
        arg: type | None = None

        if value and value is not inspect.Parameter.empty:
            from magicgui.type_map import _is_subclass

            orig = get_origin(value)
            if not (_is_subclass(orig, list) or isinstance(orig, list)):
                raise TypeError(
                    f"cannot set annotation {value} to {type(self).__name__}."
                )
            args = get_args(value)
            if len(args) > 0:
                arg = args[0]
            else:
                arg = None

        self._annotation = value
        self._args_type = arg

    def _append_value(self, value=UNSET):
        """Create a new child value widget and append it."""
        i = len(self) - 2

        widget = create_widget(
            annotation=self._args_type,
            name=f"value_{i}",
            options=self._child_options,
        )

        if isinstance(widget, EmptyWidget):
            raise TypeError("could not determine the type of child widget.")

        self.insert(i, widget)

        # Value must be set after new widget is inserted because it could be
        # valid only after same parent is shared between widgets.
        if value is UNSET and i > 0:
            value = self[i - 1].value  # type: ignore
        if value is not UNSET:
            widget.value = value

    def _pop_value(self):
        """Delete last child value widget."""
        try:
            self.pop(-3)
        except IndexError:
            pass

    @property
    def value(self) -> list:
        """Return current value as a list object."""
        return list(ListDataView(self))

    @value.setter
    def value(self, vals: Iterable[_V]):
        del self[:-2]
        for v in vals:
            self._append_value(v)

    @property
    def data(self) -> ListDataView[_V]:
        """Return a data view of current value."""
        return ListDataView(self)

    @data.setter
    def data(self, vals: Iterable[_V]):
        del self[:-2]
        for v in vals:
            self._append_value(v)


class ListDataView(Generic[_V]):
    """Data view of ListEdit."""

    def __init__(self, obj: ListEdit):
        self._obj = obj
        self._widgets: list[ValueWidget] = list(obj[:-2])  # type: ignore

    def __repr__(self):
        """Return list-like representation."""
        return f"{self.__class__.__name__}({list(self)!r})"

    def __len__(self):
        """Length as a list."""
        return len(self._widgets)

    def __eq__(self, other):
        """Compare as a list."""
        return list(self) == other

    @overload
    def __getitem__(self, i: int) -> _V:  # noqa
        ...

    @overload
    def __getitem__(self, key: slice) -> list[_V]:  # noqa
        ...

    def __getitem__(self, key):
        """Slice as a list."""
        if isinstance(key, int):
            return self._widgets[key].value
        elif isinstance(key, slice):
            return [w.value for w in self._widgets[key]]
        else:
            raise TypeError(
                f"list indices must be integers or slices, not {type(key).__name__}"
            )

    @overload
    def __setitem__(self, key: int, value: _V) -> None:  # noqa
        ...

    @overload
    def __setitem__(self, key: slice, value: _V | Iterable[_V]) -> None:  # noqa
        ...

    def __setitem__(self, key, value):
        """Update widget value."""
        if isinstance(key, int):
            self._widgets[key].value = value
        elif isinstance(key, slice):
            if isinstance(value, type(self._widgets[0].value)):
                for w in self._widgets[key]:
                    w.value = value
            else:
                for w, v in zip(self._widgets[key], value):
                    w.value = v
        else:
            raise TypeError(
                f"list indices must be integers or slices, not {type(key).__name__}"
            )

    @overload
    def __delitem__(self, key: int) -> None:  # noqa
        ...

    @overload
    def __delitem__(self, key: slice) -> None:  # noqa
        ...

    def __delitem__(self, key):
        """Delete widget at the key(s)."""
        self._obj.__delitem__(key)

    def __iter__(self) -> Iterator[_V]:
        """Iterate over values of child widgets."""
        for w in self._widgets:
            yield w.value


@merge_super_sigs
class TupleEdit(Container):
    """A widget to represent a tuple of values.

    A TupleEdit container has several child widgets of different type. Their value is
    represented as a Python tuple object. If a tuple is given as the initial value,
    types of child widgets are determined one by one. Unlike ListEdit, number of
    contents is not editable.

    Parameters
    ----------
    options: WidgetOptions, optional
        Widget options of child widgets.
    """

    def __init__(
        self,
        value: Iterable[_V] | _Unset = UNSET,
        layout: str = "horizontal",
        nullable: bool = False,
        options: WidgetOptions = None,
        **kwargs,
    ):
        self._nullable = nullable
        self._args_types: tuple[type, ...] | None = None
        super().__init__(layout=layout, labels=False, **kwargs)
        self._child_options = options or {}
        self.margins = (0, 0, 0, 0)

        if not isinstance(value, _Unset):
            if self._args_types is None:
                self._args_types = tuple(type(a) for a in value)
            _value: Iterable[Any] = value
        elif self._args_types is not None:
            _value = (UNSET,) * len(self._args_types)
        else:
            raise ValueError(
                "Either 'value' or 'annotation' must be specified in "
                f"{type(self).__name__}."
            )

        for i, a in enumerate(_value):
            i = len(self)
            widget = create_widget(
                value=a,
                annotation=self._args_types[i],
                name=f"value_{i}",
                options=self._child_options,
            )
            self.insert(i, widget)

    def __iter__(self) -> Iterator[ValueWidget]:
        """Just for typing."""
        return super().__iter__()  # type: ignore

    @property
    def annotation(self):
        """Return type annotation for the parameter represented by the widget.

        ForwardRefs will be resolve when setting the annotation. For TupleEdit,
        annotation will be like 'tuple[str, int]'.
        """
        return self._annotation

    @annotation.setter
    def annotation(self, value):
        if value is None:
            self._annotation = None
            self._args_types = None
            return
        from .._type_wrapper import resolve_annotation

        value = resolve_annotation(value)
        args: tuple[type, ...] | None = None

        if value and value is not inspect.Parameter.empty:
            from magicgui.type_map import _is_subclass

            orig = get_origin(value)
            if not (_is_subclass(orig, tuple) or isinstance(orig, tuple)):
                raise TypeError(
                    f"cannot set annotation {value} to {type(self).__name__}."
                )
            args = get_args(value)
            value = Tuple[args]

        self._annotation = value
        self._args_types = args

    @property
    def value(self) -> tuple:
        """Return current value as a tuple."""
        return tuple(w.value for w in self)

    @value.setter
    def value(self, vals: Sequence):
        if len(vals) != len(self):
            raise ValueError("Length of tuple does not match.")

        for w, v in zip(self, vals):
            w.value = v  # type: ignore


class _LabeledWidget(Container):
    """Simple container that wraps a widget and provides a label."""

    def __init__(
        self,
        widget: Widget,
        label: str = None,
        position: str = "left",
        **kwargs,
    ):
        kwargs["layout"] = "horizontal" if position in ("left", "right") else "vertical"
        self._inner_widget = widget
        widget._labeled_widget_ref = ref(self)
        _visible = False if widget._explicitly_hidden else None
        self._label_widget = Label(value=label or widget.label, tooltip=widget.tooltip)
        super().__init__(**kwargs, visible=_visible)
        self.parent_changed.disconnect()  # don't need _LabeledWidget to trigger stuff
        self.labels = False  # important to avoid infinite recursion during insert!
        self._inner_widget.label_changed.connect(self._on_label_change)
        for w in [self._label_widget, widget]:
            with w.parent_changed.blocked():
                self.append(w)
        self.margins = (0, 0, 0, 0)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"Labeled{self._inner_widget!r}"

    @property
    def value(self):
        return getattr(self._inner_widget, "value", None)

    @value.setter
    def value(self, value):
        if hasattr(self._inner_widget, "value"):
            self._inner_widget.value = value  # type: ignore

    @property
    def label(self):
        return self._label_widget.label

    @label.setter
    def label(self, label):
        self._label_widget.label = label

    def _on_label_change(self, value: str):
        self._label_widget.value = value

    @property
    def label_width(self):
        return self._label_widget.width

    @label_width.setter
    def label_width(self, width):
        self._label_widget.min_width = width
