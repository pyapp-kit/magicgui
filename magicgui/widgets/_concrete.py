"""Widgets backed by a backend implementation, ready to be instantiated by the user.

All of these widgets should provide the `widget_type` argument to their
super().__init__ calls.
"""
import inspect
import math
import os
import sys
from pathlib import Path
from typing import Callable, List, Sequence, Tuple, Type, TypeVar, Union, overload
from weakref import ref

from docstring_parser import DocstringParam, parse
from typing_extensions import Literal

from magicgui.application import use_app
from magicgui.types import FileDialogMode, PathLike
from magicgui.widgets._bases.mixins import _ReadOnlyMixin

from ._bases import (
    ButtonWidget,
    CategoricalWidget,
    ContainerWidget,
    MainWindowWidget,
    RangedWidget,
    SliderWidget,
    TransformedRangedWidget,
    ValueWidget,
    Widget,
)
from ._transforms import make_float, make_literal_eval

BUILDING_DOCS = sys.argv[-2:] == ["build", "docs"]


def _param_list_to_str(param_list: List[DocstringParam]) -> str:
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
    param_docs: List[DocstringParam] = []
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
    cls: Type[C],
    widget_name: str = None,
    transform: Callable[[Type], Type] = None,
) -> Type[C]:
    ...


@overload
def backend_widget(  # noqa
    cls: Literal[None] = None,
    widget_name: str = None,
    transform: Callable[[Type], Type] = None,
) -> Callable[..., Type[C]]:
    ...


def backend_widget(
    cls: Type[C] = None,
    widget_name: str = None,
    transform: Callable[[Type], Type] = None,
) -> Union[Callable, Type[C]]:
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

    def wrapper(cls) -> Type[Widget]:
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
        return f"{self.widget_type}" + f"(name={self.name!r})" if self.name else ""


@backend_widget
class Label(ValueWidget):
    """A non-editable text or image display."""


@backend_widget
class LineEdit(ValueWidget):
    """A one-line text editor."""


@backend_widget(widget_name="LineEdit", transform=make_literal_eval)
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


@backend_widget(widget_name="Slider", transform=make_float)
class FloatSlider(SliderWidget):
    """A slider widget to adjust a float value within a range."""


@merge_super_sigs
class LogSlider(TransformedRangedWidget):
    """A slider widget to adjust a numerical value logarithmically within a range.

    Parameters
    ----------
    base : Enum, Iterable, or Callable
        The base to use for the log, by default math.e.
    """

    def __init__(
        self, min: float = 1, max: float = 100, base: float = math.e, **kwargs
    ):
        for key in ("maximum", "minimum"):
            if key in kwargs:
                import warnings

                warnings.warn(
                    f"The {key!r} keyword arguments has been changed to {key[:3]!r}. "
                    "In the future this will raise an exception\n",
                    FutureWarning,
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
class Container(ContainerWidget):
    """A Widget to contain other widgets."""


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
        self, mode: FileDialogMode = FileDialogMode.EXISTING_FILE, filter=None, **kwargs
    ):
        self.line_edit = LineEdit(value=kwargs.pop("value", None))
        self.choose_btn = PushButton()
        self.mode = mode  # sets the button text too
        self.filter = filter
        kwargs["widgets"] = [self.line_edit, self.choose_btn]
        kwargs["labels"] = False
        kwargs["layout"] = "horizontal"
        super().__init__(**kwargs)
        self.margins = (0, 0, 0, 0)
        self._show_file_dialog = use_app().get_obj("show_file_dialog")
        self.choose_btn.changed.connect(self._on_choose_clicked)

    @property
    def mode(self) -> FileDialogMode:
        """Mode for the FileDialog."""
        return self._mode

    @mode.setter
    def mode(self, value: Union[FileDialogMode, str]):
        self._mode = FileDialogMode(value)
        self.choose_btn.text = self._btn_text

    @property
    def _btn_text(self) -> str:
        if self.mode is FileDialogMode.EXISTING_DIRECTORY:
            return "Choose directory"
        else:
            return "Select file" + ("s" if self.mode.name.endswith("S") else "")

    def _on_choose_clicked(self, event=None):
        _p = self.value
        start_path: Path = _p[0] if isinstance(_p, tuple) else _p
        _start_path = os.fspath(start_path.expanduser().absolute())
        result = self._show_file_dialog(
            self.mode,
            caption=self._btn_text,
            start_path=_start_path,
            filter=self.filter,
        )
        if result:
            self.value = result

    @property
    def value(self) -> Union[Tuple[Path, ...], Path]:
        """Return current value of the widget.  This may be interpreted by backends."""
        text = self.line_edit.value
        if self.mode is FileDialogMode.EXISTING_FILES:
            return tuple(Path(p) for p in text.split(", "))
        return Path(text)

    @value.setter
    def value(self, value: Union[Sequence[PathLike], PathLike]):
        """Set current file path."""
        if isinstance(value, (list, tuple)):
            value = ", ".join([os.fspath(p) for p in value])
        if not isinstance(value, (str, Path)):
            raise TypeError(
                f"value must be a string, or list/tuple of strings, got {type(value)}"
            )
        self.line_edit.value = os.fspath(Path(value).expanduser().absolute())

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<FileEdit mode={self.mode.value!r}, value={self.value!r}>"


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

    def __init__(self, start=0, stop=10, step=1, **kwargs):
        self.start = SpinBox(value=start)
        self.stop = SpinBox(value=stop)
        self.step = SpinBox(value=step)
        kwargs["widgets"] = [self.start, self.stop, self.step]
        super().__init__(**kwargs)

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
    """A widget to represent range objects, with start/stop/step.

    slice(stop)
    slice(start, stop[, step])

    Slice objects may be used for extended slicing (e.g. a[0:10:2])
    """

    @property  # type: ignore
    def value(self) -> slice:  # type: ignore
        """Return current value of the widget.  This may be interpreted by backends."""
        return slice(self.start.value, self.stop.value, self.step.value)

    @value.setter
    def value(self, value: slice):
        """Set current file path."""
        self.start.value = value.start
        self.stop.value = value.stop
        self.step.value = value.step


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
            with w.parent_changed.blocker():
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

    def _on_label_change(self, event):
        self._label_widget.value = event.value

    @property
    def label_width(self):
        return self._label_widget.width

    @label_width.setter
    def label_width(self, width):
        self._label_widget.min_width = width
