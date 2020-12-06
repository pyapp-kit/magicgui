"""[summary]


"""
import inspect
import os
from functools import wraps
from pathlib import Path
from typing import Any, Sequence, Tuple, Type, Union

from magicgui import transforms
from magicgui.application import use_app
from magicgui.types import FileDialogMode, PathLike

from ._bases import (
    ButtonWidget,
    CategoricalWidget,
    ContainerWidget,
    RangedWidget,
    SliderWidget,
    ValueWidget,
    Widget,
)

_widget_doc = """{}

    Parameters
    ----------
    name : str, optional
        The name of the parameter represented by this widget. by default ""
    kind : str, optional
        The ``inspect._ParameterKind`` represented by this widget.  Used in building
        signatures from multiple widgets, by default "POSITIONAL_OR_KEYWORD"
    default : Any, optional
        The default & starting value for the widget, by default None
    annotation : Any, optional
        The type annotation for the parameter represented by the widget, by default None
    gui_only : bool, optional
        Whether the widget should be considered "only for the gui", or if it should be
        included in any widget container signatures, by default False"""

_button_widget_doc = _widget_doc
_button_widget_doc += """
    text : str, optional
        The text to display on the button. by default "Text\""""

_range_widget_doc = _widget_doc
_range_widget_doc += """
    minimum : float, optional
        The minimum allowable value, by default 0
    maximum : float, optional
        The maximum allowable value, by default 100
    step : float, optional
        The step size for incrementing the value, by default 1"""

_slider_widget_doc = _range_widget_doc
_slider_widget_doc += """
    orientation : str, {{'horizontal', 'vertical'}}
        The orientation for the slider, by default "horizontal\""""

_combo_box_doc = _widget_doc
_combo_box_doc += """
    choices : Enum, Iterable, or Callable
        Available choices displayed in the combo box."""


def backend_widget(cls=None, widget_name=None, transform=None):
    """[summary]

    Parameters
    ----------
    cls : [type], optional
        The class being decorated, by default None.
    widget_name : [type], optional
        The name of the backend widget to wrap. If None, the name of the class being
        decorated is used.  By default None.
    transform : [type], optional
        [description], by default None

    Returns
    -------
    [type]
        [description]
    """

    @wraps(cls)
    def wrapper(cls) -> Type[Widget]:
        def __init__(self, **kwargs):
            app = use_app()
            assert app.native
            widget = app.get_obj(widget_name or cls.__name__)
            if transform:
                widget = transform(widget)
            kwargs["widget_type"] = widget
            super(cls, self).__init__(**kwargs)

        params = {}
        for klass in reversed(inspect.getmro(cls)):
            sig = inspect.signature(getattr(klass, "__init__"))
            for name, param in sig.parameters.items():
                if name in ("self", "widget_type", "kwargs", "args", "kwds"):
                    continue
                params[name] = param

        cls.__init__ = __init__
        cls.__signature__ = inspect.Signature(
            sorted(params.values(), key=lambda x: x.kind)
        )
        return cls

    return wrapper(cls) if cls else wrapper


@backend_widget
class Label(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format("A non-editable text or image display.")


@backend_widget
class LineEdit(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format("A one-line text editor.")


@backend_widget(widget_name="LineEdit", transform=transforms.make_literal_eval)
class LiteralEvalLineEdit(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format(
        "A one-line text editor that evaluates strings as python literals."
    )


@backend_widget
class TextEdit(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format(
        "A widget to edit and display both plain and rich text."
    )


@backend_widget
class DateTimeEdit(ValueWidget):  # noqa: D101
    __doc__ = _widget_doc.format("A widget for editing dates and times.")


@backend_widget
class PushButton(ButtonWidget):  # noqa: D101
    __doc__ = _button_widget_doc.format("A command button.")


@backend_widget
class CheckBox(ButtonWidget):  # noqa: D101
    __doc__ = _button_widget_doc.format("A checkbox with a text label.")


@backend_widget
class RadioButton(ButtonWidget):  # noqa: D101
    __doc__ = _button_widget_doc.format("A radio button with a text label")


@backend_widget
class SpinBox(RangedWidget):  # noqa: D101
    __doc__ = _range_widget_doc.format(
        "A widget to edit an integer with clickable up/down arrows."
    )


@backend_widget
class FloatSpinBox(RangedWidget):  # noqa: D101
    __doc__ = _range_widget_doc.format(
        "A widget to edit a float with clickable up/down arrows."
    )


@backend_widget
class Slider(SliderWidget):  # noqa: D101
    __doc__ = _slider_widget_doc.format(
        "A slider widget to adjust a numerical value within a range."
    )


@backend_widget(widget_name="Slider", transform=transforms.make_float)
class FloatSlider(SliderWidget):  # noqa: D101
    __doc__ = _slider_widget_doc.format(
        "A slider widget to adjust a float value within a range."
    )


@backend_widget(widget_name="Slider", transform=transforms.make_log)
class LogSlider(SliderWidget):  # noqa: D101
    __doc__ = _slider_widget_doc.format(
        "A slider widget to adjust a numerical value logarithmically within a range."
    )


@backend_widget
class ComboBox(CategoricalWidget):  # noqa: D101
    __doc__ = _combo_box_doc.format(
        "A categorical widget, allowing selection between multiple choices."
    )


@backend_widget
class Container(ContainerWidget):  # noqa: D101
    pass


class FileEdit(Container):
    """A LineEdit widget with a button that opens a FileDialog."""

    def __init__(
        self,
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = inspect.Parameter.empty,
        annotation=None,
        gui_only=False,
        orientation="horizontal",
        mode: FileDialogMode = FileDialogMode.EXISTING_FILE,
        label=None,
    ):
        self.line_edit = LineEdit()
        self.choose_btn = PushButton()
        self.mode = mode  # sets the button text too
        super().__init__(
            orientation=orientation,
            widgets=[self.line_edit, self.choose_btn],
            name=name,
            kind=kind,
            default=default,
            annotation=annotation,
            gui_only=gui_only,
            label=label,
        )
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
        start_path = os.fspath(start_path.expanduser().absolute())
        result = self._show_file_dialog(
            self.mode, caption=self._btn_text, start_path=start_path
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


class RangeEdit(Container):
    """A widget to represent range objects, with start/stop/step."""

    def __init__(
        self,
        name: str = "",
        kind: str = "POSITIONAL_OR_KEYWORD",
        default: Any = inspect.Parameter.empty,
        annotation=None,
        gui_only=False,
        orientation="horizontal",
        start=0,
        stop=10,
        step=1,
    ):
        self.start = SpinBox(default=start)
        self.stop = SpinBox(default=stop)
        self.step = SpinBox(default=step)
        super().__init__(
            orientation=orientation,
            widgets=[self.start, self.stop, self.step],
            name=name,
            kind=kind,
            default=default,
            annotation=annotation,
            gui_only=gui_only,
        )

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
        return f"<RangeEdit value={self.value!r}>"


class SliceEdit(RangeEdit):
    """A widget to represent range objects, with start/stop/step."""

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

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<SliceEdit value={self.value!r}>"
